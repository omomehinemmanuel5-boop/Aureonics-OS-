import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://lex.aureonics.ai';
  const now = new Date();
  return [
    { url: `${base}/`, lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${base}/demo`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/pricing`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${base}/app`, lastModified: now, changeFrequency: 'daily', priority: 0.8 },
    { url: `${base}/enterprise`, lastModified: now, changeFrequency: 'weekly', priority: 0.8 }
  ];
}
