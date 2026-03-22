import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const books = defineCollection({
	loader: glob({ base: './src/content/books', pattern: '**/*.{md,mdx}' }),
	schema: ({ image }) =>
		z.object({
			title: z.string(),
			slug: z.string(),
			author: z.string(),
			isbn13: z.string().optional(),
			publisher: z.string().optional(),
			datePublished: z.string().optional(),
			coverImage: z.optional(image()),
			series: z.string().optional(),
			seriesOrder: z.number().optional(),
			whyRead: z.string().optional(),
			banReasons: z.array(z.string()),
			banLocations: z.array(
				z.object({
					state: z.string(),
					district: z.string().optional(),
					year: z.number().optional(),
					sourceUrl: z.string().optional(),
				})
			),
			totalChallenges: z.number(),
			description: z.string(),
			// Legacy single links (still supported)
			amazonUrl: z.string().optional(),
			bookshopUrl: z.string().optional(),
			capitalBooksUrl: z.string().optional(),
			// New: multiple editions/formats
			buyLinks: z.array(
				z.object({
					label: z.string(),
					amazon: z.string().optional(),
					bookshop: z.string().optional(),
					capitalBooks: z.string().optional(),
					other: z.string().optional(),
				})
			).optional(),
		}),
});

export const collections = { books };
