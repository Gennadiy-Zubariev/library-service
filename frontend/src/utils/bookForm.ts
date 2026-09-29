export function buildBookFormData(fields: {
  title: string;
  author: string;
  cover: string;
  inventory: number;
  dailyFee: string;
  image: File | null;
}): FormData {
  const data = new FormData();
  data.append("title", fields.title);
  data.append("author", fields.author);
  data.append("cover", fields.cover);
  data.append("inventory", String(fields.inventory));
  data.append("daily_fee", fields.dailyFee);
  if (fields.image) data.append("image", fields.image);
  return data;
}
