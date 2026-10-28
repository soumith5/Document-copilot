import { visit } from 'unist-util-visit'

const CITATION_PATTERN = /\[(\d+)\]/g

/**
 * A remark plugin: finds "[1]", "[2]" style markers the LLM was instructed
 * to emit (see assistant/instructions.md rule #5) inside plain text nodes,
 * and replaces them with a custom "citationRef" node, rendered as a
 * clickable badge by MessageContent.tsx's `components` override.
 *
 * Uses loose (any) types for the syntax tree here rather than importing
 * mdast's types directly — mdast isn't a direct dependency (only pulled
 * in transitively via react-markdown), and pnpm's strict node_modules
 * layout doesn't expose it for our own type-only import.
 */
export function remarkCitationRefs() {
  return (tree: any) => {
    visit(tree, 'text', (node: any, index: number | undefined, parent: any) => {
      if (!parent || typeof index !== 'number') return
      if (!CITATION_PATTERN.test(node.value)) return
      CITATION_PATTERN.lastIndex = 0

      const newNodes: any[] = []
      let lastIndex = 0
      let match: RegExpExecArray | null

      while ((match = CITATION_PATTERN.exec(node.value)) !== null) {
        if (match.index > lastIndex) {
          newNodes.push({ type: 'text', value: node.value.slice(lastIndex, match.index) })
        }
        newNodes.push({
          type: 'citationRef',
          data: {
            hName: 'citation-ref',
            hProperties: { 'data-citation-number': match[1] },
          },
          children: [{ type: 'text', value: match[1] }],
        })
        lastIndex = match.index + match[0].length
      }
      if (lastIndex < node.value.length) {
        newNodes.push({ type: 'text', value: node.value.slice(lastIndex) })
      }

      parent.children.splice(index, 1, ...newNodes)
    })
  }
}