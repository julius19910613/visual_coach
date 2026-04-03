/**
 * EdgeOne Pages entry point.
 * Uses hono-edgeone-pages-adapter to handle requests.
 */
import { handle } from 'hono-edgeone-pages-adapter';
import app from '../src/index';

export const onRequest = handle(app);
