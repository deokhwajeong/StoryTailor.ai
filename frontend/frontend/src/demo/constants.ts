// Demo builds (vite build --mode demo, or VITE_DEMO=1) swap the Flask API for
// an in-browser mock. Kept separate from mockApi.ts so the normal build never
// pulls in the sample stories or the catalog.
export const IS_DEMO = import.meta.env.MODE === 'demo' || import.meta.env.VITE_DEMO === '1';

// Fictional access code for the demo reader. Any 8 characters work.
export const DEMO_ACCESS_CODE = 'DEMO2026';

export const DEMO_TOPIC_IDEAS = [
  'an octopus who loves puzzles',
  'a trip to the Moon',
  'an owl who makes a new friend',
  'a seed that will not grow',
  'a dragon at the library',
];
