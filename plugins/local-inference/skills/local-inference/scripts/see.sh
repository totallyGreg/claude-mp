#!/bin/zsh
# see.sh — the `see` tier: read an image with a local model.
#
#   see.sh --text --schema FILE IMAGE [PROMPT]   letters in the image (receipt, form, screenshot of text):
#                                                fields → JSON
#   see.sh [--schema FILE] IMAGE [PROMPT]        meaning in pixels (chart, diagram, photo): plain vision
#   see.sh --code IMAGE                          QR/barcode → its exact payload (always fm)
#   --with-text                                  wrap the answer as {"answer": …, "read_text": …} with what
#                                                fm's OCR/barcode tool actually read, to check values against
#   --fm | --omlx                                force a backend (default: oMLX's :fast if the server is up,
#                                                else fm; --code and --with-text always use fm)
#
# Backends: the oMLX `:fast` profile (a vision model; ~2.7× faster, same accuracy on text — tiers.md
# derivation 13) or Apple's on-device model (`fm`, macOS 27: OCR and barcode tools, no server).
# FILE may be ordinary JSON Schema; for fm the fields Apple's dialect requires (title,
# additionalProperties, x-order, required) are filled in. Every listed field is required — a field the
# image doesn't have gets invented (an absent "tip" came back as the tax), so ask only for what is printed.
# Exit: 0 ok, 1 model failed, refused, or (--text/--code) fm's tool read nothing, 2 usage,
#       3 no backend available (fm missing and oMLX down or not chosen).
set -u
mode=pixels schema= with_text=0 backend=auto
OMLX=http://127.0.0.1:8000
while (( $# )); do
  case $1 in
    --text) mode=text ;;
    --code) mode=code ;;
    --schema) schema=${2:-}; shift ;;
    --with-text) with_text=1 ;;
    --fm) backend=fm ;;
    --omlx) backend=omlx ;;
    -h|--help) sed -n '2,20p' $0 | sed 's/^# \{0,1\}//'; exit 0 ;;
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
if [[ $mode == code ]] || (( with_text )); then
  [[ $backend == omlx ]] && { print -u2 "see: --code and --with-text need fm's OCR/barcode tools; drop --omlx"; exit 2; }
  backend=fm
fi

tmp=$(mktemp -d "${TMPDIR:-/tmp}/see.XXXXXX")
trap 'rm -rf $tmp' EXIT

# oMLX: the :fast profile's vision model. Field descriptions go in the prompt too —
# json_schema output constrains the shape but the model never sees the descriptions.
omlx_see() {
  local key model img=$image mime=image/png s=null
  key=$(/usr/bin/jq -r '.auth.api_key // empty' ~/.omlx/settings.json 2>/dev/null)
  [[ -n $key ]] || return 3
  model=${SEE_MODEL:-$(/usr/bin/curl -s -m 3 -H "Authorization: Bearer $key" $OMLX/v1/models |
    /usr/bin/jq -r '[.data[]?.id | select(endswith(":fast"))][0] // empty' 2>/dev/null)}
  [[ -n $model ]] || return 3
  case ${image:l} in
    *.png) ;;
    *.jpg|*.jpeg) mime=image/jpeg ;;
    *) /usr/bin/sips -s format jpeg $image --out $tmp/img.jpg >/dev/null 2>&1 || return 1
       img=$tmp/img.jpg mime=image/jpeg ;;
  esac
  /usr/bin/base64 -i $img > $tmp/img.b64 || return 1
  if [[ -n $schema ]]; then
    s=$(/usr/bin/jq -c 'del(.["$schema"])' $schema) || { print -u2 "see: schema is not valid JSON"; exit 2; }
  fi
  local p=$prompt
  [[ -z $p && $mode == text ]] && p='Extract the fields from this image.'
  [[ -z $p ]] && p='Describe this image.'
  /usr/bin/jq -n --rawfile b64 $tmp/img.b64 --arg mime $mime --arg model $model --arg p $p --argjson s $s '
    {model: $model, temperature: 0, max_tokens: 1024, chat_template_kwargs: {enable_thinking: false},
     messages: [{role: "user", content: [
       {type: "image_url", image_url: {url: ("data:" + $mime + ";base64," + ($b64 | gsub("\\s"; "")))}},
       {type: "text", text: (if $s then $p + "\nReturn JSON matching this schema; follow each field description:\n" + ($s | tojson) else $p end)}]}]}
    + (if $s then {response_format: {type: "json_schema", json_schema: {name: "result", schema: $s}}} else {} end)' > $tmp/body.json
  /usr/bin/curl -s -m 120 -H "Authorization: Bearer $key" -H 'Content-Type: application/json' \
    -d @$tmp/body.json $OMLX/v1/chat/completions > $tmp/resp.json || return 1
  /usr/bin/jq -er '.choices[0].message.content // empty' $tmp/resp.json > $tmp/out 2>/dev/null || return 1
  [[ -z $schema ]] || /usr/bin/jq -e . $tmp/out >/dev/null 2>&1 || return 1
  cat $tmp/out
}

if [[ $backend != fm ]]; then
  omlx_see; rc=$?
  (( rc == 0 )) && exit 0
  if (( rc == 3 )); then reason='oMLX is down or has no :fast profile'; else reason='oMLX failed'; fi
  [[ $backend == omlx ]] && { print -u2 "see: $reason"; exit $rc; }
  (( rc == 3 )) || print -u2 "see: $reason; using fm"
fi

if [[ ! -x /usr/bin/fm ]] || ! /usr/bin/fm available >/dev/null 2>&1; then
  print -u2 "see: Apple's fm is unavailable (needs macOS 27 and, once, \`sudo fm license\`)"; exit 3
fi
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
