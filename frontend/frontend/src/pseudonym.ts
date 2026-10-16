// Readable display names for pseudonymous student ids, derived only from the id
// (an FNV-1a hash into two short word lists), so the same student always reads as
// the same name and no new data is stored. "stu_174d450131bd" might show as
// "Jade Heron". These are display labels, not real names, and the teacher view
// keeps the underlying id one hover or tap away.

const COLORS = [
  'Amber', 'Aqua', 'Berry', 'Blue', 'Cedar', 'Cloud', 'Cobalt', 'Copper',
  'Coral', 'Fern', 'Golden', 'Green', 'Hazel', 'Honey', 'Indigo', 'Ivory',
  'Jade', 'Lilac', 'Maple', 'Mint', 'Moss', 'Olive', 'Pearl', 'Plum',
  'Rose', 'Ruby', 'Saffron', 'Sage', 'Silver', 'Sky', 'Teal', 'Willow',
];

const ANIMALS = [
  'Badger', 'Beaver', 'Bison', 'Crane', 'Dolphin', 'Falcon', 'Finch', 'Fox',
  'Gecko', 'Hare', 'Heron', 'Ibis', 'Jay', 'Kiwi', 'Koala', 'Lemur',
  'Llama', 'Lynx', 'Marten', 'Moose', 'Newt', 'Ocelot', 'Orca', 'Otter',
  'Owl', 'Panda', 'Penguin', 'Puffin', 'Quail', 'Robin', 'Seal', 'Sparrow',
  'Swan', 'Tapir', 'Turtle', 'Walrus', 'Wren', 'Yak', 'Zebra', 'Koi',
];

function fnv1a(text: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  // Final avalanche step (from MurmurHash3) so ids that differ only slightly
  // still spread across both word lists.
  h ^= h >>> 16;
  h = Math.imul(h, 0x85ebca6b) >>> 0;
  h ^= h >>> 13;
  h = Math.imul(h, 0xc2b2ae35) >>> 0;
  h ^= h >>> 16;
  return h >>> 0;
}

export function displayName(id: string): string {
  const h = fnv1a(id);
  return `${COLORS[h % COLORS.length]} ${ANIMALS[Math.floor(h / COLORS.length) % ANIMALS.length]}`;
}

// Names for a whole class. Two ids can land on the same name, so any name used
// more than once gets the last characters of its id appended; the result is
// still deterministic for a given roster.
export function displayNames(ids: string[]): Map<string, string> {
  const counts = new Map<string, number>();
  for (const id of ids) counts.set(displayName(id), (counts.get(displayName(id)) ?? 0) + 1);
  return new Map(ids.map(id => {
    const name = displayName(id);
    return [id, (counts.get(name) ?? 0) > 1 ? `${name} ${id.slice(-3).toUpperCase()}` : name];
  }));
}
