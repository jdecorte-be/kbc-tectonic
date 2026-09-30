const size = [
  "xs",
  "sm",
  "md",
  "lg",
  "xl"
] as const

export default {
  "base": "relative",
  "variants": {
    "size": {
      "xs": "",
      "sm": "",
      "md": "",
      "lg": "",
      "xl": ""
    },
    "orientation": {
      "horizontal": "inline-flex -space-x-px",
      "vertical": "flex flex-col -space-y-px"
    }
  },
  "defaultVariants": {
    "size": "md" as typeof size[number]
  }
}