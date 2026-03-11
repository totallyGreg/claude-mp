# Confluence Storage Format Reference

All page content uses Confluence Storage Format (XHTML with `ac:` namespace macros). **Always use the Write tool to create a temp JSON file** rather than inline heredocs for large payloads.

## Text & Structure

```xml
<h2>Heading</h2>
<p>Paragraph with <strong>bold</strong>, <em>italic</em>, and <code>code</code>.</p>
<ul><li>Bullet item</li></ul>
<ol><li>Numbered item</li></ol>
<hr />
<table><tbody>
  <tr><th>Header</th><th>Header</th></tr>
  <tr><td>Cell</td><td>Cell</td></tr>
</tbody></table>
```

**Special characters:** Use `&amp;` `&ndash;` `&mdash;` `&bull;` `&rsquo;` `&ldquo;` `&rdquo;` — never raw `&`, `–`, `—`, etc.

## Panel Macro (colored box with title)

```xml
<ac:structured-macro ac:name="panel" ac:schema-version="1">
  <ac:parameter ac:name="bgColor">#f0f5ff</ac:parameter>
  <ac:parameter ac:name="titleBGColor">#0052CC</ac:parameter>
  <ac:parameter ac:name="titleColor">#ffffff</ac:parameter>
  <ac:parameter ac:name="title">Panel Title</ac:parameter>
  <ac:parameter ac:name="borderStyle">solid</ac:parameter>
  <ac:parameter ac:name="borderColor">#0052CC</ac:parameter>
  <ac:rich-text-body><p>Content here</p></ac:rich-text-body>
</ac:structured-macro>
```

## Info / Note / Warning / Tip Panels

```xml
<!-- Info (blue) -->
<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:parameter ac:name="icon">true</ac:parameter>
  <ac:parameter ac:name="title">Info Title</ac:parameter>
  <ac:rich-text-body><p>Informational content</p></ac:rich-text-body>
</ac:structured-macro>

<!-- Note (yellow) -->
<ac:structured-macro ac:name="note" ac:schema-version="1">
  <ac:parameter ac:name="title">Note Title</ac:parameter>
  <ac:rich-text-body><p>Note content</p></ac:rich-text-body>
</ac:structured-macro>

<!-- Warning (red) -->
<ac:structured-macro ac:name="warning" ac:schema-version="1">
  <ac:parameter ac:name="title">Warning Title</ac:parameter>
  <ac:rich-text-body><p>Warning content</p></ac:rich-text-body>
</ac:structured-macro>

<!-- Tip (green) -->
<ac:structured-macro ac:name="tip" ac:schema-version="1">
  <ac:parameter ac:name="title">Tip Title</ac:parameter>
  <ac:rich-text-body><p>Tip content</p></ac:rich-text-body>
</ac:structured-macro>
```

## Status Macro (colored badge)

```xml
<ac:structured-macro ac:name="status" ac:schema-version="1">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">ACTIVE</ac:parameter>
</ac:structured-macro>
```

Colors: `Green`, `Blue`, `Red`, `Yellow`, `Purple`, `Grey`

## Expand Macro (collapsible section)

```xml
<ac:structured-macro ac:name="expand" ac:schema-version="1">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body><p>Hidden content</p></ac:rich-text-body>
</ac:structured-macro>
```

## Code Block

```xml
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:parameter ac:name="title">Code Title</ac:parameter>
  <ac:plain-text-body><![CDATA[echo "hello world"]]></ac:plain-text-body>
</ac:structured-macro>
```

Languages: `bash`, `python`, `java`, `javascript`, `json`, `yaml`, `xml`, `sql`, `go`, `ruby`, `html`, `css`, `none`

## Table of Contents

```xml
<ac:structured-macro ac:name="toc" ac:schema-version="1">
  <ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>
```

## Layout Sections

```xml
<!-- Single column -->
<ac:layout><ac:layout-section ac:type="single"><ac:layout-cell>
  <p>Full width content</p>
</ac:layout-cell></ac:layout-section></ac:layout>

<!-- Two equal columns -->
<ac:layout><ac:layout-section ac:type="two_equal">
  <ac:layout-cell><p>Left column</p></ac:layout-cell>
  <ac:layout-cell><p>Right column</p></ac:layout-cell>
</ac:layout-section></ac:layout>

<!-- Three equal columns -->
<ac:layout><ac:layout-section ac:type="three_equal">
  <ac:layout-cell><p>Col 1</p></ac:layout-cell>
  <ac:layout-cell><p>Col 2</p></ac:layout-cell>
  <ac:layout-cell><p>Col 3</p></ac:layout-cell>
</ac:layout-section></ac:layout>

<!-- Sidebar layouts -->
<!-- ac:type options: two_left_sidebar, two_right_sidebar -->
```

Multiple layout sections can be stacked within a single `<ac:layout>` tag.

## Emoticon

```xml
<ac:emoticon ac:name="blue-star" />
<ac:emoticon ac:name="green-star" />
<ac:emoticon ac:name="warning" />
<ac:emoticon ac:name="tick" />
<ac:emoticon ac:name="cross" />
<ac:emoticon ac:name="information" />
```

## Recently Updated Macro

```xml
<ac:structured-macro ac:name="recently-updated" ac:schema-version="1" />
```

## Page Tree & Search

```xml
<ac:structured-macro ac:name="pagetree" ac:schema-version="1" />
<ac:structured-macro ac:name="pagetreesearch" ac:schema-version="1" />
```

## Children Display

```xml
<ac:structured-macro ac:name="children" ac:schema-version="1">
  <ac:parameter ac:name="all">true</ac:parameter>
  <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>
```

## Excerpt

```xml
<ac:structured-macro ac:name="excerpt" ac:schema-version="1">
  <ac:parameter ac:name="hidden">true</ac:parameter>
  <ac:rich-text-body><p>This text can be included on other pages</p></ac:rich-text-body>
</ac:structured-macro>
```

## Link to Another Confluence Page

```xml
<ac:link><ri:page ri:content-title="Page Title" ri:space-key="SPACEKEY" /><ac:plain-text-link-body><![CDATA[Display Text]]></ac:plain-text-link-body></ac:link>
```

## User Mention

```xml
<ac:link><ri:user ri:username="USERNAME" /></ac:link>
```
