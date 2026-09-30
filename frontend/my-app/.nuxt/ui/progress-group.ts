const color = [
  "primary",
  "secondary",
  "success",
  "info",
  "warning",
  "error",
  "neutral"
] as const

const size = [
  "2xs",
  "xs",
  "sm",
  "md",
  "lg",
  "xl",
  "2xl"
] as const

const orientation = [
  "horizontal",
  "vertical"
] as const

export default {
  "slots": {
    "root": "gap-2",
    "base": "flex overflow-hidden rounded-full bg-accented",
    "segment": "duration-200 ease-out motion-reduce:transition-none",
    "indicator": "size-full",
    "status": "flex text-dimmed duration-200 ease-out motion-reduce:transition-none",
    "list": "flex flex-col gap-1",
    "item": "flex items-center gap-1.5 min-w-0",
    "itemLeadingIcon": "shrink-0",
    "itemLeadingDot": "shrink-0 rounded-full",
    "itemLabel": "truncate",
    "itemTrailing": "ms-auto shrink-0 text-dimmed"
  },
  "variants": {
    "color": {
      "primary": {
        "indicator": "bg-primary",
        "itemLeadingIcon": "text-primary",
        "itemLeadingDot": "bg-primary"
      },
      "secondary": {
        "indicator": "bg-secondary",
        "itemLeadingIcon": "text-secondary",
        "itemLeadingDot": "bg-secondary"
      },
      "success": {
        "indicator": "bg-success",
        "itemLeadingIcon": "text-success",
        "itemLeadingDot": "bg-success"
      },
      "info": {
        "indicator": "bg-info",
        "itemLeadingIcon": "text-info",
        "itemLeadingDot": "bg-info"
      },
      "warning": {
        "indicator": "bg-warning",
        "itemLeadingIcon": "text-warning",
        "itemLeadingDot": "bg-warning"
      },
      "error": {
        "indicator": "bg-error",
        "itemLeadingIcon": "text-error",
        "itemLeadingDot": "bg-error"
      },
      "neutral": {
        "indicator": "bg-inverted",
        "itemLeadingIcon": "text-highlighted",
        "itemLeadingDot": "bg-inverted"
      }
    },
    "size": {
      "2xs": {
        "status": "text-xs",
        "list": "text-xs",
        "itemLeadingIcon": "size-3",
        "itemLeadingDot": "size-1.5"
      },
      "xs": {
        "status": "text-xs",
        "list": "text-xs",
        "itemLeadingIcon": "size-3",
        "itemLeadingDot": "size-1.5"
      },
      "sm": {
        "status": "text-sm",
        "list": "text-sm",
        "itemLeadingIcon": "size-4",
        "itemLeadingDot": "size-2"
      },
      "md": {
        "status": "text-sm",
        "list": "text-sm",
        "itemLeadingIcon": "size-4",
        "itemLeadingDot": "size-2"
      },
      "lg": {
        "status": "text-sm",
        "list": "text-sm",
        "itemLeadingIcon": "size-4",
        "itemLeadingDot": "size-2"
      },
      "xl": {
        "status": "text-base",
        "list": "text-base",
        "itemLeadingIcon": "size-5",
        "itemLeadingDot": "size-2.5"
      },
      "2xl": {
        "status": "text-base",
        "list": "text-base",
        "itemLeadingIcon": "size-5",
        "itemLeadingDot": "size-2.5"
      }
    },
    "orientation": {
      "horizontal": {
        "root": "w-full flex flex-col",
        "base": "w-full flex-row",
        "segment": "h-full transition-[width]",
        "status": "flex-row items-center justify-end w-(--percent) min-w-fit transition-[width]"
      },
      "vertical": {
        "root": "h-full flex flex-row",
        "base": "h-full flex-col",
        "segment": "w-full transition-[height]",
        "status": "flex-col justify-end h-(--percent) min-h-fit transition-[height]"
      }
    }
  },
  "compoundVariants": [
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "2xs" as typeof size[number],
      "class": "h-px"
    },
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "xs" as typeof size[number],
      "class": "h-0.5"
    },
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "sm" as typeof size[number],
      "class": "h-1"
    },
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "md" as typeof size[number],
      "class": "h-2"
    },
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "lg" as typeof size[number],
      "class": "h-3"
    },
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "xl" as typeof size[number],
      "class": "h-4"
    },
    {
      "orientation": "horizontal" as typeof orientation[number],
      "size": "2xl" as typeof size[number],
      "class": "h-5"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "2xs" as typeof size[number],
      "class": "w-px"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "xs" as typeof size[number],
      "class": "w-0.5"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "sm" as typeof size[number],
      "class": "w-1"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "md" as typeof size[number],
      "class": "w-2"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "lg" as typeof size[number],
      "class": "w-3"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "xl" as typeof size[number],
      "class": "w-4"
    },
    {
      "orientation": "vertical" as typeof orientation[number],
      "size": "2xl" as typeof size[number],
      "class": "w-5"
    }
  ],
  "defaultVariants": {
    "color": "primary" as typeof color[number],
    "size": "md" as typeof size[number]
  }
}