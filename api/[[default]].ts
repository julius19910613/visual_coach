/**
 * EdgeOne Pages Node Functions entry point.
 * Delegates all requests to the Hono app.
 */
import app from '../src/index';

export default app.fetch.bind(app);
