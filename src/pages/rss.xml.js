import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { SITE_TITLE, SITE_DESCRIPTION } from '../consts';

export async function GET(context) {
	const books = await getCollection('books');
	return rss({
		title: SITE_TITLE,
		description: SITE_DESCRIPTION,
		site: context.site,
		items: books.map((book) => ({
			title: `${book.data.title} - BANNED`,
			pubDate: book.data.datePublished ? new Date(book.data.datePublished) : new Date(),
			description: book.data.description,
			link: `/isitbanned/books/${book.data.slug}`,
		})),
	});
}
