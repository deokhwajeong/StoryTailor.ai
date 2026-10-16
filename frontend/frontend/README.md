# StoryTailor student app

React + Vite + Tailwind front end for the student reading flow: enter the reading
code from your teacher, ask for a story, read it, and say whether it was too easy,
just right, or too hard.

```bash
npm install
VITE_API_URL=http://localhost:5000 npm run dev
```

The access code is kept in memory only. Nothing is written to localStorage or cookies.

## Demo build (no backend)

`npm run build:demo` builds a static copy in `dist-demo/` where API calls are served by
the in-browser mock in `src/demo/mockApi.ts`. It uses a relative base path, so the folder
can be hosted anywhere, for example https://deokhwajeong.github.io/demos/storytailor/.
`npm run dev:demo` runs the same mode locally. The normal `npm run build` does not
include the mock or the sample stories.
