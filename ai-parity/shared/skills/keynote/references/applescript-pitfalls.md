# Keynote AppleScript pitfalls

Read this reference before writing custom AppleScript outside the bundled helpers.

## Preserve document identity and state

- Address a deck by file name when several documents are open. Never assume `document 1`
  is the intended presentation.
- Convert `POSIX file` values outside `tell application "Keynote"`; Keynote's terminology can
  shadow AppleScript coercions.
- When opening from an argv path, `open` may not return a usable document reference. Open the
  file, then resolve `document deckName` explicitly.
- Record whether the deck was already open. Close it after a scripted operation only when the
  script opened it; otherwise preserve the user's live review state.
- The legacy bridge's export command closes the document. The preview helper reopens it.

## Pass external values safely

Pass paths and user-authored text through `osascript` argv whenever possible. Quotes,
backslashes, LaTeX, and newlines are fragile when interpolated into `osascript -e` source.
The bundled layout helper uses argv; the bridge applies explicit AppleScript-string escaping.

```bash
osascript - "$TITLE" "$BODY" <<'APPLESCRIPT'
on run argv
    set slideTitle to item 1 of argv
    set slideBody to item 2 of argv
    tell application "Keynote"
        -- use slideTitle and slideBody
    end tell
end run
APPLESCRIPT
```

Do string splitting outside `tell application "Keynote"`. Keynote defines its own `text item`
class, which can shadow AppleScript's `text item delimiters` behavior.

## Work with placeholders and custom items

- Themed slides can expose invisible or master-derived shapes. Do not identify a shape only
  by `shape 1`.
- Match custom text by a distinctive content marker, or use geometry from the rich inventory.
- Default title/body placeholders can also appear in the `text items` collection. Filter items
  whose text and geometry duplicate the default placeholders.
- Set an object's position as a complete `{x, y}` pair. Keynote rejects assignments to
  `item 1 of position` or `item 2 of position`.
- Apply text style and accessibility metadata before locking an object; a locked object rejects
  later `set` commands.

## Images and object reuse

- Keynote embeds an image at insertion time. Changing the source file does not update the slide.
  Delete and reinsert the image while preserving its position and dimensions.
- Use `file name` and accessibility description to distinguish images when several are present.
- Shapes cannot reliably be copied with `duplicate shape`. Duplicate the whole slide when the
  exact theme styling must be preserved, then replace its content.
- LaTeX equations have no supported Keynote AppleScript insertion API. Use a clearly labeled
  placeholder and presenter note for manual Insert > Equation conversion.

## Formatting limitations

- Set font, size, and color on `object text`, not on the container alone.
- Handle default title, default body, and custom text items separately.
- Shape background fill is readable but not generally writable through the current dictionary.
- Rotation, opacity, reflection, position, width, height, and locking are available for several
  item classes; support varies by class, so wrap custom operations in `try` blocks.
- Transition properties accept a record containing effect, duration, delay, and automatic state.

## Verification

- Save only after every operation in a mutation succeeds. On error, close without saving when
  the script opened the deck.
- Export changed slides to images and inspect the downscaled results.
- Re-run rich inventory after custom scripting to confirm geometry, text, notes, image metadata,
  slide layout, and skipped state.
