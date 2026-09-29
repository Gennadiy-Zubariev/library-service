from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand

from books.models import Book

SEED_IMAGES_DIR = Path(__file__).resolve().parents[2] / "seed_images"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

# (image file name without extension, title, author, cover, inventory, daily_fee)
BOOKS = [
    ("the-hobbit", "The Hobbit", "J.R.R. Tolkien", "HARD", 5, "1.50"),
    ("1984", "1984", "George Orwell", "SOFT", 7, "1.00"),
    ("dune", "Dune", "Frank Herbert", "HARD", 4, "2.00"),
    ("pride-and-prejudice", "Pride and Prejudice", "Jane Austen", "SOFT", 6, "0.90"),
    ("the-great-gatsby", "The Great Gatsby", "F. Scott Fitzgerald", "HARD", 3, "1.20"),
    ("to-kill-a-mockingbird", "To Kill a Mockingbird", "Harper Lee", "SOFT", 5, "1.10"),
    (
        "crime-and-punishment",
        "Crime and Punishment",
        "Fyodor Dostoevsky",
        "SOFT",
        4,
        "0.80",
    ),
    ("dracula", "Dracula", "Bram Stoker", "SOFT", 3, "0.90"),
    ("frankenstein", "Frankenstein", "Mary Shelley", "SOFT", 4, "0.90"),
    (
        "the-catcher-in-the-rye",
        "The Catcher in the Rye",
        "J.D. Salinger",
        "SOFT",
        5,
        "1.00",
    ),
    ("brave-new-world", "Brave New World", "Aldous Huxley", "HARD", 4, "1.30"),
    ("moby-dick", "Moby-Dick", "Herman Melville", "HARD", 2, "1.40"),
    (
        "the-little-prince",
        "The Little Prince",
        "Antoine de Saint-Exupery",
        "HARD",
        8,
        "0.70",
    ),
    ("kobzar", "Kobzar", "Taras Shevchenko", "HARD", 6, "0.60"),
    ("forest-song", "Forest Song", "Lesya Ukrainka", "SOFT", 3, "0.60"),
    (
        "shadows-of-forgotten-ancestors",
        "Shadows of Forgotten Ancestors",
        "Mykhailo Kotsiubynsky",
        "SOFT",
        3,
        "0.70",
    ),
]


def find_image(slug):
    for ext in IMAGE_EXTENSIONS:
        path = SEED_IMAGES_DIR / f"{slug}{ext}"
        if path.exists():
            return path
    return None


class Command(BaseCommand):
    help = (
        "Seed the database with sample books, an admin and a regular user. "
        "Cover images are taken from books/seed_images/<image-name>.jpg|png|webp."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true", help="Delete all books first."
        )

    def handle(self, *args, **options):
        if options["flush"]:
            Book.objects.all().delete()
            self.stdout.write("Deleted all books.")

        self._seed_users()
        self._seed_books()

    def _seed_users(self):
        User = get_user_model()
        for email, password, staff, first, last in (
            ("admin@library.com", "admin12345", True, "Admin", "User"),
            ("user@library.com", "user12345", False, "Test", "Reader"),
        ):
            if User.objects.filter(email=email).exists():
                continue
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first,
                last_name=last,
                is_staff=staff,
                is_superuser=staff,
            )
            self.stdout.write(f"Created user {user.email} / {password}")

    def _seed_books(self):
        created = with_image = 0
        missing = []
        for slug, title, author, cover, inventory, fee in BOOKS:
            book, was_created = Book.objects.update_or_create(
                title=title,
                author=author,
                defaults={"cover": cover, "inventory": inventory, "daily_fee": fee},
            )
            created += was_created

            path = find_image(slug)
            if path is None:
                missing.append(slug)
            elif not book.image:
                with path.open("rb") as f:
                    book.image.save(path.name, File(f), save=True)
                with_image += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Books: {len(BOOKS)} total, {created} new, {with_image} images attached."
            )
        )
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f"No image in {SEED_IMAGES_DIR} for: {', '.join(missing)}"
                )
            )
