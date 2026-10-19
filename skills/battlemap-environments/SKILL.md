---
name: battlemap-environments
description: Use when building an outdoor Dungeondraft scene such as a forest, shoreline, trail, ruin exterior, or open encounter map.
---

# Dungeondraft environments

**Scale vegetation from its texture size before you scatter it.** Asset
footprints vary enormously and nothing warns you. A tree texture may be a few
hundred pixels or several thousand, and at 256 woxels per tile that is the
difference between a shrub two tiles wide and a canopy nine tiles wide — wider
than a small building. Scattered at whatever scale looks reasonable, the large
ones stop reading as trees in a forest and become a lid over the map; their
shadows fall as broad dark bands that get mistaken for terrain, and bare trunks
stick out from under them with no crown in sight.

Never assume a family shares a size, and never carry a number over from another
map: read `sizes` from `list_assets` (or `texture_size` from `get_element`) for
the assets you actually chose, decide how many TILES the thing should occupy,
and set the scale from that:

    scale = desired_tiles * 256 / texture_px

Say the intended canopy size in tiles when you plan a treeline. A tree larger
than the building beside it is a composition error, not a detail.

**Keep canopies off the buildings.** A tree on a canopy layer (700 and up) draws
over walls, windows and the room inside them. Scatter trees with
`scatter_objects(wall_margin=0)`, which keeps each object's whole reach — half
its diagonal, times its scale, so any turn of it — off every wall, and `avoid_rects` for a
road or a door's approach. Without them the rectangle bounds only the centres,
not the crowns. `validate_placements` reports a canopy over a wall under
`crossing_walls` and over a window under `blocking_portals`.

Make the land readable before making it busy. Terrain layering, a dominant
silhouette and a clear route should survive a whole-map view before incidental
detail is added. Follow the shared [build loop](../_shared/build-loop.md) so
macro masses, clusters and accents each receive a visual checkpoint.

## Compose the ground

Set a [material language](../battlemap-material-language/SKILL.md) before
choosing terrain, water, vegetation, or landmark assets so the scene has a
deliberate field, supporting texture, and focal contrast.

Set a [lighting hierarchy](../battlemap-lighting-hierarchy/SKILL.md) before
adding sources so weather, route choices, and the landmark use darkness and
contrast deliberately.

Use at least three terrain slots for open ground — a base, a worn or dry
variant where feet and wheels go, and a third for damp, moss or stone — and
blend them where they meet. One texture across the whole map reads as a
placeholder however well the objects sit on it.

Read the climate from the style bible before choosing any of them. It decides
the base (sand and flagstone in a dry city, mud and grass in a wet one), how
much grows and where — in a dry place, green only where someone waters it —
and whether water is everyday or precious.

**Judge the grass by its colour, not its name.** The base grass sets the
season for the whole map. Summer grass is a saturated green; an olive or
yellowed base makes an entire meadow read dead or parched, however lush the
planting on top of it. Look at the candidates with
`preview_assets(category='Terrain')`, then paint a small patch of the favourite
and judge it in a screenshot before committing, because changing a slot's
texture later changes everything already painted with it. Keep dirt to where
feet actually go, and give a darker variant of the same grass a paintable slot
for patches, hollows and the ground under trees, so the meadow has tone without
changing material.

1. Use `list_assets` to find only the terrain, water, vegetation and landmark
   families that fit the style bible.
2. Establish terrain layering with broad ground regions first. Treat water and
   terrain transitions as compositional edges, not as decorative afterthoughts.
   At a water or material boundary, make a transition band rather than tracing
   the outline exactly: use `paint_terrain` in a supporting terrain slot with
   uneven, overlapping soft strokes, vary its width, then interrupt parts of it
   with the base terrain. Use `get_terrain` on each side of the boundary and a
   screenshot to confirm deliberate material variation without obscuring the
   intended water edge. At a river or pond the band is the bank itself; see
   [Rivers and waterfalls read by their edges](#rivers-and-waterfalls-read-by-their-edges).
3. Place the largest silhouette next: a treeline mass, rock formation, ruin,
   cliff or water body that frames the focal event.
4. Shape each route to lead to, through or around the focal event. Keep token
   movement and sight lines legible; use negative space as intentional breathing
   room rather than filling every surface.

## A building has a site, not a margin

When the map contains a structure, the outside is not the space left over once
the walls are up. It is where the building *is*, and treating it as a border to
decorate is what makes a finished interior sit in a void — every count correct,
every asset placed, and nothing around it that explains why anything is there.

Before dressing the exterior, answer three things and build the answers:

1. **How do people reach it?** A road, a track, a river landing, a mountain
   path. It should enter at one map edge and leave at another, so the building
   sits *on* a route rather than at the end of one that exists only for it.
2. **Where do they arrive?** Find the exterior doors and read what they are
   for. The main entrance wants an approach and somewhere to stand — a
   forecourt, a porch, a yard. That is also where arrival-related props belong:
   a trough where riders stop, a sign facing the road.
3. **Where does the work happen?** Most buildings have a public side and a
   working one. A service door wants a yard, and the yard wants the things its
   work needs — a well, a cart, fuel, stores — connected back to the route.

Then let the ground record the use. Bare earth where feet and wheels go, worn
grass at the edges of it, unbroken ground where nobody walks. Ground that shows
where people move does more for believability than any amount of scattered
detail, and it is what makes the difference between a building on a map and a
building in a place.

**A walled property's street is a region of its own.** Plan the far side of
the wall with a purpose list: who passes (carts, porters, the watch), who
stops (water-sellers, a beggar, riders at a hitching rail), and what the
owner gives back to the street (a public fountain by the gate, a lamp, a
shrine). Give it a carriageway and pavements with ruts turning in at the gate,
and frontages opposite — a shop, a rival's workshop, a warehouse with a wagon
backed up. The outside face of the wall is where the household's status shows,
so dress the street rather than the wall itself.

Work the exterior before the interior when you can: the site decides where the
doors matter, and a door that turns out to face nothing is expensive to move
once the rooms behind it are furnished.

## Blend ground edges, and know which edge can never blend

A path laid as a floor PATTERN cannot blend into anything. A pattern sits above
the terrain, so its border stays a dead straight cut however much you paint
beside it — measured, by painting soft grass strokes across a pattern path's
edge and seeing none of it arrive. Keep patterns for floors under a roof, and
make outdoor ground — paths, yards, tracks — out of TERRAIN, which does blend.

Then there is the trap that makes blending look impossible. Slot 0 is the base
and is NOT paintable: `paint_terrain(slot=0)` is accepted and changes nothing.
So if `fill_terrain` put grass in slot 0, you cannot paint grass back over a
path's edge. Assign grass to a paintable slot as well (slot 2, say), and paint
THAT along the edge — a soft brush, `rate` around 0.8, strokes of uneven length
and depth. The result is grass reaching into the path in an irregular line,
which is what a real verge looks like.

`path_blender_01` to `04`, in the Paths category, exist for exactly this: drawn
along a seam they feather one material into the next. Use one where two grounds
meet and the join still reads as a line someone drew.

**Under textured blending, a step in weight draws a line.** With the level on
textured blending (`set_terrain_blending(enabled=False)`), every hard step in
a slot's weight renders as a thin dark seam: a region filled at `rate` 0.85
beside one at 1.0 leaves an outline along the join that nobody drew. Fill
neighbouring regions at the same rate, and soften a boundary with a few large,
soft `paint_terrain` dabs rather than many small ones. The terrain splat is
coarse — about 64 woxels per pixel on a typical map — so a dab under roughly
200 woxels radius comes out as a blocky square instead of a soft disc. Smooth
blending (`enabled=True`) has no seams but less grain; it is a per-level
setting that redraws every edge already painted, so choose it before painting.

## Weathering is sparse brushwork

Ground that has seen weather carries grit, sand or leaf litter where the wind
and the traffic leave it, not everywhere. Wind piles it against vertical faces
and into corners: the foot of a wall, a courtyard's corners, the lee of a
gate, the kerb. Traffic sweeps the middle of a path clean. So weather a hard
surface with many small `paint_terrain` dabs at low `rate` (about 0.2-0.5),
of uneven radius, where the material would collect, and save full coverage
for the verges and open ground outside the walls.

Plan the slots for it when you lay the ground. The base slot 0 cannot take
paint, so a durable base (flagstone, cobbles) goes in slot 0 and the
weathering material in a paintable slot from the start, because changing a
slot's texture later changes everything already painted with it. Weathering is subtle at map
zoom, so judge it in a screenshot framed at token scale.

## Caves are carved, not built

A cave is not a room with rocky walls. `dig_cave` takes a POLYLINE and a radius
and opens the rock along it, so you shape a cave the way water would: a passage
that wanders, chambers where it widens, dead ends that go nowhere. A cave drawn
as a rectangle reads as a basement.

- **Dig the route first, then widen.** One stroke along the whole path at a
  small radius, then second passes with a larger radius where you want a
  chamber. Digging chamber-by-chamber leaves them connected by nothing.
- **A single point is a chamber.** `points` with one pair digs one circular
  space — that is the documented behaviour and the way to place a rotunda or a
  pocket off a passage.
- **Set the rock's colours with the dig**, not after: `ground_color` and
  `wall_color` on the same call, plus `texture` for the cave floor. They decide
  whether it reads as limestone, basalt or packed earth.
- **Connect it to the outside deliberately.** A cave mouth is where the carved
  rock meets open ground, and it only reads as an entrance if the ground
  outside leads to it — a path, worn terrain, or a widening of the passage as
  it reaches daylight. After digging the route, use `set_cave_entrance` at its
  border to blast a circular opening through the rocky edge. The mask removes
  border art without carving floor; set its `open` argument to false to
  restore the edge. `get_cave` reports floor and entrance cell counts and the
  actual ground/wall colours. Confirm the floor count stays unchanged, then
  frame the mouth in a screenshot to verify a usable approach. A mask away
  from an existing cave border may produce no visible opening.
- **`dig=False` fills rock back in.** That is how to take back an over-wide
  chamber; there is no delete for carved rock. The parameter is `dig`, not
  `erase` — an unknown argument is dropped silently at the tool boundary, so
  naming the wrong one digs MORE rock rather than failing.

Check it with an `export_map`: a cave's shape is the thing being judged, and
element counts say nothing about it at all. Blend the approach with terrain
and sparse material detail after the route and entrance read clearly. Cave
undo retains both bitmaps; select the original level before undoing, and do
not try to restore cave history across a map resize.

## Rivers and waterfalls read by their edges

Water is recognised by its banks, not by the colour of its middle. A water body
laid straight onto grass reads as a blue shape painted on a lawn; the same body
with a cut bank and a band of shallows reads as a river at a glance. Build the
edge in three parts, from the land inward:

1. **An earth cut along both banks.** A thin brown band where the ground drops
   to the water, drawn with `draw_path` along each shore. CrossHead packs ship
   dirt-cliff paths for this, e.g. `terrain_dirt_cliff` in CH Seasons; find
   what this map can use with `list_assets(category='Paths')` and
   `search_pack_contents` for "cliff", "bank" and "edge".
2. **A light shallows band just inside the edge.** A river-edge path drawn just
   inside the waterline, such as `river_edge` from Into The Woods, so the water
   pales where it is shallow.
3. **A darker deep middle.** `set_water_style(deep_color=..., shallow_color=...)`
   after `add_water`, so the channel darkens away from the banks.

**Keep the bed smooth.** Terrain painted under `add_water` shows through it, so
gravel or cobbles under the water draw a cobbled riverbed across the whole
channel. Leave plain earth or the base under the water and let rocks supply the
texture. A wide gravel band along the shore is not how a bank is drawn either:
the transition band at a river is the cut and the shallows, a tile or less, with
the grass meeting the cut directly.

**Rivers meander and change width.** A straight channel of even width reads as
a canal. Let the river bend, narrow where it runs fast — at rapids, and at the
crossing, which is why a bridge stands there — and widen into a round plunge
pool under a fall. Give it what real water has: a tributary joining it, an
island splitting the flow (`add_water(invert=True)` cuts one out), a slack bay
on the inside of a bend. Draw the outline with `add_water(points=...)` and put
that variation into the points; a `rect` is only ever a pool.

**Rocks live in and at the water, in clusters.** A cluster is one large rock
with two to four smaller ones against it. Put them where the water meets
something: the outside of bends, the bridge abutments, the foot of a fall, with
a scatter of small stones in the bed. Lay rock ledges across the stream where
it steps down and give each a white foam line — search for "foam" or "splash"
decals — so the water visibly breaks over it. A single big boulder alone on
open grass reads as stamped, however well it is scaled.

**Falls come from the terrain, so give a stream several.** A fall is where a
stream crosses a tier line (see the next section). A stepped landscape gives one
stream many small falls, each with its pool, its foam and its rocks at the
foot, and that reads as land; one tall fall in the middle of flat ground reads
as a set piece.

## Elevation is contour lines

Height on a top-down map is drawn the way a survey map draws it: as continuous
lines where the ground steps. Every terrace edge has to go somewhere — off the
map edge, closed on itself around a rise, or into water. A cliff that stops in
mid-field reads as a wall someone forgot to finish, because ground does not end
a drop in open grass; if one must end, cap it with a spill of rubble and rocks
so the eye accepts a slope down.

- **Thick, layered faces read as height.** Draw a cliff two or three tiles
  deep: a rock-top path along the lip over a rock-base path along the foot, or
  a run of stone cliff objects. A single thin rock line reads as a kerb. Search
  `list_assets(category='Paths')` and `search_pack_contents` for "cliff",
  "rock" and "ledge", and preview a top and a base from one art family together.
- **Draw cliff-lip walls with `shadow=False`.** A wall is what makes a cliff
  block movement and sight in a VTT, but an outdoor rock wall drawn with the
  default `shadow=True` lays a lighter, square-ended band about a tile wide
  along one side, which reads as a strip of paving beside the cliff.
- **Stairs go into the face, not along it.** Cut a notch into the cliff and run
  the steps perpendicular to the face, with a landing where they arrive, so a
  token can see where the climb starts and ends.

## A crossing is one span, and water has to read as water

A bridge is a single continuous span, or deliberately overlapping segments. Two
placed end to end leave a visible seam down the middle at map zoom, and a
reviewer reads that as one bridge that failed rather than two that met.

Check the span against the water, not against the gap you imagined: place it,
then look. A crossing that stops short of either bank is worse than no bridge,
because it says the map was never examined.

Put the bridge where a builder would: perpendicular to the flow, at a narrow
point, both ends resting on the banks, with rocks at its four corners where the
abutments meet the water. Let the road widen to the bridge's width as it
arrives rather than meeting it as a thinner line. Look at the bridge art first:
some is drawn with a row of posts or piers across the middle of the span, which
stands posts in the water wherever the river is wider than the art expected.
Roads and tracks are 2-4 tiles wide, with soft verges painted into their edges
rather than a ruled border.

And confirm the water READS as water in a render. Under a dark ambient, a
water body can come back as a grey-green band indistinguishable from shadowed
ground — one map's central river was mistaken for a tree's shadow by the person
reviewing it, and the bridge appeared to cross nothing. `get_status` reporting
`layers.water: true` only means water exists somewhere; it says nothing about
whether a viewer can tell.

**Water has to match the map's art family too.** `add_water` draws
Dungeondraft's own water, with its own look, and beside painterly art a small
formal pond in it can read as belonging to another map. For small, still,
formal water — a reflecting pool, a fountain basin, a garden pond — prefer
the art family's water pattern with `place_pattern`, set inside a stone kerb,
with the family's lily pads or reeds on it. Keep `add_water` for large or
moving water, where its shoreline blending earns its place, and compare
either in a render against the rest of the map.

**Frozen water is a material, not water.** An iced-over stream, a frozen pond
or a sheet of ice is `paint_material` with a Materials asset such as
`textures/materials/ice_tile.png`. Its defaults, layer -400 and a smooth edge,
are the right ones: the patch sits below the banks and cliffs, and their paths
overlap its edge so the ice reads as tucked under them. `add_water` gives
moving water with ripples and a shoreline, which is the wrong substance.
Building a frozen stream from water bodies gets both the look and the
behaviour wrong; one ice material stroke is the right tool.

## Nothing grows on a map by itself

An exterior can pass every structural check and still look like mown municipal
lawn, because being correct and being alive are different problems. Every
installation carries far more ground cover than a build usually reaches for —
grasses, fallen leaves and branches, roots, shrubs, vines, ferns, flowers,
mushrooms, thorns. Find out what THIS map can use rather than assuming: search
`list_assets` for each family in turn. What exists depends on the Dungeondraft
version and on which packs the map includes, so a list memorised from another
map will be wrong somewhere.

- **Plants grow where feet and wheels do not.** Against walls, in corners, along
  fences, at the foot of anything that stands still, and at the edges of paths —
  not scattered evenly across open ground.
- **Wear goes where they do.** Bare earth at a door, a gate, a trough, a
  well; grass thinning to dirt where a track is actually walked.
- **Clusters, not confetti.** Three clusters of five read as growth; fifteen
  singles spread evenly read as a texture someone applied.
- **Give the ground evidence of a life.** A woodpile, a barrow, crates by a
  door, washing, a cart with its shafts down. One or two of these say more about
  who lives here than another dozen shrubs. An open encounter map needs the
  same evidence to give the fight a reason: a camp (tents, a campfire,
  crates), a ruin, a cart, a boat drawn up at a landing — beside the route, in
  the clearing, where it explains why anyone stopped here.

- **A plant on hard ground needs a bed.** Soil, a planter or a kerbed border
  under every planted cluster on paving; plants straight on flagstone read as
  pasted on. Shape the bed to the planting — a long rounded rectangle under a
  hedge row, an irregular oval under a cluster — with `place_pattern` or a
  soil terrain slot. Fit it to the plants' `opaque_bounds` from `get_element`,
  which cover the foliage itself; pack art often fills half its canvas, so
  positions and canvas `bounds` put the bed off centre.

Ground detail is a fine sprinkle, not a handful of big props: flower specks,
grass tufts, the darker grass under trees, small and many. A quiet zone is
sparse, not sterile: it still gets tufts and litter, just fewer, smaller, and
further apart.

**Planting has a register, and it should match who keeps the place.** A
wealthy or formal property is groomed: clipped hedges, contained beds, plants
in pots, edges kept. Climbing vines, self-sown growth and plants spilling over
paving belong to neglect, poverty or the wild, and a heavy hand with them
makes a cared-for courtyard read as abandoned. Decide the register from the
owner's status and upkeep, and keep to it.

**Plants never pass through walls.** Painterly bushes and trees render well
past their named tile, so a row set "along" a wall clips into it. Keep each
plant's centre at least half its rendered width (`texture_size` times scale)
from the wall line, then read `crossing_walls` in `validate_placements`.

## Detail by zone

Cluster foliage, debris and cover according to the zone’s purpose. Contrast
quiet approaches with active encounter areas and use controlled asymmetry so
the composition reads as natural without becoming visually noisy. Preserve real
walls, portals and lights wherever the requested map needs VTT behavior.
Make barriers, openings and lights reinforce the intended route and focal
hierarchy instead of treating them as isolated decoration.

Group vegetation and debris into clusters of a few, with varied scale and some
ground texture beneath them. Isolated shrubs at regular intervals read as
stamped however few there are — and a large `min_gap` in `scatter_objects`
produces exactly that, because it enforces even spacing. To make a region
sparse, place *fewer clusters* rather than the same count spread evenly: keep
`min_gap` small inside a cluster and leave real ground between clusters.

**Trees frame the map; the middle is the clearing.** Mass the canopy densely
along the map edges and over the banks, crowns overlapping, varied in size and
tone, so the woodland closes the frame and the open middle is left for combat.
Every tree needs a cast shadow under it. Some packs ship the shadow as its own
object — CrossHead's `tree_shadow_*`, for instance — to place under the crown
and offset away from the light; search the vegetation families this map uses
for "shadow". A crown with no shadow sits on the ground like a sticker.

Hand-placed rocks, logs and plants need the same variation `scatter_objects`
gives for free: a scale spread of about 0.85-1.15 at least, and angles off the
quarter turns. One size at one angle reads as stamped, however well spaced.

Capture a `screenshot` at encounter scale and use `export_map` for the
whole-map check. Run the
[composition audit](../battlemap-composition-audit/SKILL.md) before final
review. Repair only a visible defect in hierarchy, routes, water edges or
coverage; then capture again before finishing.
