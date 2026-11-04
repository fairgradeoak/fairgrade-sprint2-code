export const DEMO_EXAM_ID = '11111111-1111-4111-8111-111111111111';
export const DEMO_STUDENT_ID = '22222222-2222-4222-8222-222222222222';
export const DEMO_INSTRUCTOR_ID = '33333333-3333-4333-8333-333333333333';
export const isUuid = value => typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
export function requireUuid(value, name = 'ID') { if (!isUuid(value)) throw Error(`${name} must be a UUID`); return value.toLowerCase(); }
