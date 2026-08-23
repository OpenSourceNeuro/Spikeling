# Draft-safe Spikeling call-to-action integration

Last audited: 23 August 2026. This document proposes editorial changes; it does
not modify an existing page, Elementor template, menu or global setting.

## Existing published state

The published Spikeling redesign is available at:

`https://www.opensourceneuro.com/index.php/spikeling-atomic-redesign-draft-unpublished/`

Despite the words “draft” and “unpublished” in its title and URL, this page is
actually **published**. Treat every change to it as a production modification.

There are exactly two links labelled `Try the emulator`. Both currently point to:

`https://github.com/OpenSourceNeuro/Spikeling/releases/latest`

That destination downloads or describes desktop releases; it does not open the
browser emulator. Do not change these two links during draft-only QA.

The original existing Spikeling page is also published:

`https://www.opensourceneuro.com/index.php/spikeling/`

Neither existing published page loads emulator JavaScript, worker assets or
styles. Preserve that isolation unless a specifically approved page is intended
to embed the emulator itself.

## Destination requirements

The future button destination must:

1. Be the confirmed public permalink of the specifically approved emulator page.
2. Use HTTPS and the exact `www.opensourceneuro.com` website origin.
3. Resolve for a logged-out visitor without authentication or preview cookies.
4. Contain no `preview=true`, `page_id`, private draft parameters or fragments.
5. Be identical for both emulator buttons.
6. Leave an optional, separately labelled `Download desktop software` link free
   to point to the GitHub desktop release if the content owner wants one.

Never use the present authenticated preview URL as a production destination:

`https://www.opensourceneuro.com/?page_id=1196&preview=true`

## Approval-gated future sequence

Only after the owner explicitly approves publishing page 1196 and editing the
identified published redesign:

1. Confirm the final permalink, editorial title, ownership and exact page IDs.
2. Publish only the approved emulator page; do not change global Elementor
   templates, theme settings or unrelated navigation.
3. Verify the final permalink in an anonymous browser and check the worker,
   simulation controls, recording and console.
4. Retarget precisely the two existing `Try the emulator` links to that final
   public permalink. Do not bulk-replace all GitHub release links.
5. If clearer copy is desired, obtain approval for the text
   `Try the browser emulator`; keep any desktop-download link distinct.
6. Recheck both published Spikeling pages, the anonymous emulator page and asset
   isolation. Update only an explicitly approved navigation item if requested.
7. Preserve the prior desktop-release URL as the narrowly scoped editorial
   rollback target for those two buttons.

Publishing, cache invalidation, page edits and navigation updates are separate
production actions requiring the corresponding explicit permission.
