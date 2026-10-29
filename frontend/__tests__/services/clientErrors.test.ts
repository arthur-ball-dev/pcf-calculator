/**
 * API client error transformation (#47)
 *
 * The backend emits one error envelope for every failure:
 *   { error: { code, message, details }, request_id, timestamp }
 *
 * The axios response interceptor must surface error.message to the UI, keep
 * the field-level details and the request id for support, and map the HTTP
 * status to an APIErrorCode. Without an envelope (a proxy error, an empty
 * body) it falls back to the generic message for that status.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { rest } from 'msw';
import { server } from '../../__mocks__/server';
import client from '../../src/services/api/client';
import { APIError } from '../../src/services/api/errors';
import type { APIErrorResponse } from '../../src/types/api.types';

const BASE = 'http://localhost:8000/api/v1';

function envelope(
  code: string,
  message: string,
  details: APIErrorResponse['error']['details'] = []
): APIErrorResponse {
  return {
    error: { code, message, details },
    request_id: 'req_0123456789ab',
    timestamp: '2026-10-29T16:00:00+00:00',
  };
}

function respondWith(status: number, body?: unknown): void {
  server.use(
    rest.get(`${BASE}/thing`, (_req, res, ctx) =>
      body === undefined ? res(ctx.status(status)) : res(ctx.status(status), ctx.json(body))
    )
  );
}

async function failingRequest(): Promise<APIError> {
  try {
    await client.get('/api/v1/thing');
  } catch (error) {
    expect(error).toBeInstanceOf(APIError);
    return error as APIError;
  }
  throw new Error('request unexpectedly succeeded');
}

describe('API client error envelope handling', () => {
  // The client logs every request and failure in dev mode; keep the run quiet.
  beforeEach(() => {
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('404 with an envelope: NOT_FOUND with the server message and request id', async () => {
    respondWith(404, envelope('PRODUCT_NOT_FOUND', 'Product not found: prod-404'));

    const error = await failingRequest();

    expect(error.code).toBe('NOT_FOUND');
    expect(error.message).toBe('Product not found: prod-404');
    expect(error.requestId).toBe('req_0123456789ab');
  });

  it('404 without a body: NOT_FOUND with the generic message', async () => {
    respondWith(404);

    const error = await failingRequest();

    expect(error.code).toBe('NOT_FOUND');
    expect(error.message).toBe('Resource not found');
    expect(error.requestId).toBeUndefined();
  });

  it('400 with an envelope: VALIDATION_ERROR with the server message, not "[object Object]"', async () => {
    respondWith(400, envelope('VALIDATION_ERROR', 'Invalid page size'));

    const error = await failingRequest();

    expect(error.code).toBe('VALIDATION_ERROR');
    expect(error.message).toBe('Invalid page size');
  });

  it('422 with field details: VALIDATION_ERROR carrying the details list', async () => {
    const details = [
      { field: 'body.product_id', message: 'Field required', type: 'missing' },
      { field: 'body.quantity', message: 'Input should be greater than 0', type: 'greater_than' },
    ];
    respondWith(422, envelope('VALIDATION_ERROR', 'Request validation failed', details));

    const error = await failingRequest();

    expect(error.code).toBe('VALIDATION_ERROR');
    expect(error.message).toBe('Request validation failed');
    expect(error.details).toEqual(details);
  });

  it('409 with an envelope: CONFLICT with the server message', async () => {
    respondWith(409, envelope('CONFLICT', "Emission factor already exists for activity 'steel'"));

    const error = await failingRequest();

    expect(error.code).toBe('CONFLICT');
    expect(error.message).toBe("Emission factor already exists for activity 'steel'");
  });

  it('401 with an envelope: UNAUTHORIZED with the server message', async () => {
    respondWith(401, envelope('UNAUTHORIZED', 'Token has expired'));

    const error = await failingRequest();

    expect(error.code).toBe('UNAUTHORIZED');
    expect(error.message).toBe('Token has expired');
  });

  it('401 without a body: UNAUTHORIZED with the generic message', async () => {
    respondWith(401);

    const error = await failingRequest();

    expect(error.code).toBe('UNAUTHORIZED');
    expect(error.message).toBe('Authentication required. Please log in.');
  });

  it('500 with an envelope: SERVER_ERROR keeps the generic user-facing message', async () => {
    respondWith(500, envelope('INTERNAL_ERROR', 'Internal server error'));

    const error = await failingRequest();

    expect(error.code).toBe('SERVER_ERROR');
    expect(error.message).toBe('An unexpected server error occurred. Please try again later.');
    expect(error.requestId).toBe('req_0123456789ab');
  });

  it('a non-envelope JSON body is ignored and the generic message is used', async () => {
    respondWith(404, { detail: 'legacy shape' });

    const error = await failingRequest();

    expect(error.code).toBe('NOT_FOUND');
    expect(error.message).toBe('Resource not found');
  });
});
