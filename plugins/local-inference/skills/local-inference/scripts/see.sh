#!/bin/zsh
# see.sh — the `see` tier: read an image with Apple's on-device model (`fm`, macOS 27).
#
#   see.sh --text --schema FILE IMAGE [PROMPT]   letters in the image (receipt, form, screenshot of text):
#                                                OCR + schema → JSON
#   see.sh [--schema FILE] IMAGE [PROMPT]        meaning in pixels (chart, diagram, photo): plain vision
#   see.sh --code IMAGE                          QR/barcode → its exact payload
#   --with-text                                  wrap the answer as {"answer": …, "read_text": …} with what
#                                                the OCR/barcode tool actually read, to check values against
#
# FILE may be ordinary JSON Schema; the fields Apple's dialect requires (title, additionalProperties,
# x-order, required) are filled in. Every listed field is required — a field the image doesn't have
# gets invented (an absent "tip" came back as the tax), so ask only for what is printed.
# Exit: 0 ok, 1 fm failed, refused, or (--text/--code) its tool read nothing, 2 usage, 3 fm unavailable.
set -u
mode=pixels schema= with_text=0
while (( $# )); do
  case $1 in
    --text) mode=text ;;
    --code) mode=code ;;
    --schema) schema=${2:-}; shift ;;
    --with-text) with_text=1 ;;
    -h|--help) sed -n '2,16p' $0 | sed 's/^# \{0,1\}//'; exit 0 ;;
    --) shift; break ;;
    -*) print -u2 "see: unknown option $1"; exit 2 ;;
    *) break ;;
  esac
  shift
done
image=${1:-} prompt=${2:-}
[[ -f $image ]] || { print -u2 "see: no such image: ${image:-(none)}"; exit 2; }
[[ -z $schema || -f $schema ]] || { print -u2 "see: no such schema file: $schema"; exit 2; }
# OCR alone reads columns (all labels, then all numbers) and the model pairs them wrongly.
[[ $mode == text && -z $schema ]] && { print -u2 "see: --text needs --schema (OCR without a schema misreads)"; exit 2; }
if [[ ! -x /usr/bin/fm ]] || ! /usr/bin/fm available >/dev/null 2>&1; then
  print -u2 "see: Apple's fm is unavailable (needs macOS 27 and, once, \`sudo fm license\`)"; exit 3
fi

tmp=$(mktemp -d "${TMPDIR:-/tmp}/see.XXXXXX")
trap 'rm -rf $tmp' EXIT
args=(--no-stream --greedy --image $image --save-transcript $tmp/t.json)
case $mode in
  text) args+=(--tool ocr); : ${prompt:=Extract the fields from this image.} ;;
  code) args+=(--tool barcode); prompt='Read the code. Print ONLY its exact payload.' ;;
  pixels) : ${prompt:=Describe this image.} ;;
esac
if [[ -n $schema ]]; then
  # fm treats `title` as a type name: two objects with the same title become one type, so each
  # nested object is titled by its path (Result, ResultItems, ...).
  /usr/bin/jq 'def cap: (.[:1] | ascii_upcase) + .[1:];
    def fix($t): if type != "object" then .
      elif has("properties") then
        .type = "object" | .additionalProperties = false | .title = $t
        | .["x-order"] //= (.properties | keys_unsorted) | .required //= (.properties | keys_unsorted)
        | .properties |= with_entries(.key as $k | .value |= fix($t + ($k | cap)))
      elif has("items") then .items |= fix($t)
      else . end;
    del(.["$schema"]) | fix("Result")' $schema > $tmp/schema.json || { print -u2 "see: schema is not valid JSON"; exit 2; }
  args+=(--schema $tmp/schema.json)
fi

# The OCR tool fails intermittently; with greedy decoding a refusal repeats, so 3 tries is plenty.
for try in 1 2 3; do
  NO_COLOR=1 /usr/bin/fm respond $args -- $prompt > $tmp/out 2> $tmp/err && break
  [[ $mode == pixels ]] && break
done
if [[ ! -s $tmp/out ]] || grep -q '^Error:' $tmp/err; then
  err_msg=$(grep -m1 '^Error:' $tmp/err || print 'fm returned nothing')
  # fm's safety guardrails refuse benign inputs (non-English, tax notes, repeated text).
  # These are not fixable with flags — route to the oMLX tiers.
  if echo "$err_msg" | grep -qi 'guardrails\|refused'; then
    print -u2 "see: fm's safety guardrails triggered — route this image to the oMLX tiers"; exit 1
  fi
  print -u2 "see: $err_msg"; exit 1
fi
if [[ -n $schema ]] && ! /usr/bin/jq -e . $tmp/out >/dev/null 2>&1; then
  print -u2 "see: fm did not return JSON"; exit 1
fi

read_text=$(/usr/bin/jq -r '[.transcript.transcript.entries[] | select(.toolName) | .contents[]?.text // empty] | join("\n")' $tmp/t.json 2>/dev/null)
# With nothing read, the schema still gets filled — with invented empties and zeros.
if [[ $mode != pixels && -z ${read_text//[[:space:]]/} ]]; then
  print -u2 "see: the $mode tool read nothing in $image (no ${${mode:#code}:+text}${${mode:#text}:+code} found)"; exit 1
fi
if (( with_text )); then
  if [[ -n $schema ]]; then
    /usr/bin/jq -c --arg t "$read_text" '{answer: ., read_text: $t}' $tmp/out
  else
    /usr/bin/jq -nc --rawfile a $tmp/out --arg t "$read_text" '{answer: ($a | rtrimstr("\n")), read_text: $t}'
  fi
else
  cat $tmp/out
fi
