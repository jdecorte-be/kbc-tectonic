const color = [
  "primary",
  "secondary",
  "success",
  "info",
  "warning",
  "error",
  "neutral"
] as const

const variant = [
  "list",
  "card"
] as const

const indicator = [
  "start",
  "end",
  "hidden"
] as const

const size = [
  "xs",
  "sm",
  "md",
  "lg",
  "xl"
] as const

export default {
  "slots": {
    "root": "relative flex items-start",
    "container": "flex items-center",
    "base": "rounded-sm ring ring-inset ring-accented overflow-hidden focus-visible:outline-none",
    "indicator": "flex items-center justify-center size-full text-inverted" as typeof indicator[number],
    "icon": "shrink-0",
    "wrapper": "w-full",
    "label": "block font-medium text-default",
    "description": "text-muted"
  },
  "variants": {
    "color": {
      "primary": {
        "indicator": "bg-primary" as typeof indicator[number]
      },
      "secondary": {
        "indicator": "bg-secondary" as typeof indicator[number]
      },
      "success": {
        "indicator": "bg-success" as typeof indicator[number]
      },
      "info": {
        "indicator": "bg-info" as typeof indicator[number]
      },
      "warning": {
        "indicator": "bg-warning" as typeof indicator[number]
      },
      "error": {
        "indicator": "bg-error" as typeof indicator[number]
      },
      "neutral": {
        "indicator": "bg-inverted" as typeof indicator[number]
      }
    },
    "variant": {
      "list": {
        "root": ""
      },
      "card": {
        "root": [
          "border border-default rounded-lg hover:not-has-disabled:not-has-focus-visible:not-has-data-[state=checked]:bg-elevated/50",
          "transition-colors"
        ]
      }
    },
    "indicator": {
      "start": {
        "root": "flex-row",
        "wrapper": "ms-2"
      },
      "end": {
        "root": "flex-row-reverse",
        "wrapper": "me-2"
      },
      "hidden": {
        "base": "sr-only",
        "wrapper": "flex flex-col items-center gap-1 text-center"
      }
    },
    "size": {
      "xs": {
        "base": "size-3",
        "icon": "size-2.5",
        "container": "h-4",
        "wrapper": "text-xs"
      },
      "sm": {
        "base": "size-3.5",
        "icon": "size-3",
        "container": "h-4",
        "wrapper": "text-xs"
      },
      "md": {
        "base": "size-4",
        "icon": "size-3.5",
        "container": "h-5",
        "wrapper": "text-sm"
      },
      "lg": {
        "base": "size-4.5",
        "icon": "size-4",
        "container": "h-5",
        "wrapper": "text-sm"
      },
      "xl": {
        "base": "size-5",
        "icon": "size-4.5",
        "container": "h-6",
        "wrapper": "text-base"
      }
    },
    "required": {
      "true": {
        "label": "after:content-['*'] after:ms-0.5 after:text-error"
      }
    },
    "disabled": {
      "true": {
        "root": "opacity-75",
        "base": "cursor-not-allowed",
        "label": "cursor-not-allowed",
        "description": "cursor-not-allowed"
      }
    },
    "highlight": {
      "true": "",
      "false": ""
    },
    "checked": {
      "true": ""
    }
  },
  "compoundVariants": [
    {
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "container": "h-auto"
      }
    },
    {
      "variant": "card" as typeof variant[number],
      "highlight": false,
      "class": {
        "root": "hover:not-has-disabled:not-has-focus-visible:not-has-data-[state=checked]:border-accented"
      }
    },
    {
      "size": "xs" as typeof size[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "icon": "size-3"
      }
    },
    {
      "size": "sm" as typeof size[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "icon": "size-3.5"
      }
    },
    {
      "size": "md" as typeof size[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "icon": "size-4"
      }
    },
    {
      "size": "lg" as typeof size[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "icon": "size-4.5"
      }
    },
    {
      "size": "xl" as typeof size[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "icon": "size-5"
      }
    },
    {
      "size": "xs" as typeof size[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "p-2.5"
      }
    },
    {
      "size": "sm" as typeof size[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "p-3"
      }
    },
    {
      "size": "md" as typeof size[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "p-3.5"
      }
    },
    {
      "size": "lg" as typeof size[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "p-4"
      }
    },
    {
      "size": "xl" as typeof size[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "p-4.5"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-primary/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-primary"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-secondary/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-secondary"
      }
    },
    {
      "color": "success" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-success/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-success"
      }
    },
    {
      "color": "info" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-info/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-info"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-warning/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-warning"
      }
    },
    {
      "color": "error" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-error/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-error"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": [
        "start" as typeof indicator[number],
        "end" as typeof indicator[number]
      ],
      "class": {
        "base": "outline-inverted/25 focus-visible:outline-solid focus-visible:outline-3 focus-visible:ring-inverted"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-primary/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-primary has-focus-visible:z-[1]"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-secondary/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-secondary has-focus-visible:z-[1]"
      }
    },
    {
      "color": "success" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-success/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-success has-focus-visible:z-[1]"
      }
    },
    {
      "color": "info" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-info/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-info has-focus-visible:z-[1]"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-warning/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-warning has-focus-visible:z-[1]"
      }
    },
    {
      "color": "error" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-error/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-error has-focus-visible:z-[1]"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "outline-inverted/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-inverted has-focus-visible:z-[1]"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-primary/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-primary has-focus-visible:z-[1]"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-secondary/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-secondary has-focus-visible:z-[1]"
      }
    },
    {
      "color": "success" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-success/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-success has-focus-visible:z-[1]"
      }
    },
    {
      "color": "info" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-info/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-info has-focus-visible:z-[1]"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-warning/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-warning has-focus-visible:z-[1]"
      }
    },
    {
      "color": "error" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-error/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-error has-focus-visible:z-[1]"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "variant": "list" as typeof variant[number],
      "indicator": "hidden" as typeof indicator[number],
      "class": {
        "root": "outline-inverted/25 has-focus-visible:outline-3 not-has-disabled:has-focus-visible:border-inverted has-focus-visible:z-[1]"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-primary/50 has-data-[state=checked]:bg-primary/10"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-secondary/50 has-data-[state=checked]:bg-secondary/10"
      }
    },
    {
      "color": "success" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-success/50 has-data-[state=checked]:bg-success/10"
      }
    },
    {
      "color": "info" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-info/50 has-data-[state=checked]:bg-info/10"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-warning/50 has-data-[state=checked]:bg-warning/10"
      }
    },
    {
      "color": "error" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-error/50 has-data-[state=checked]:bg-error/10"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "variant": "card" as typeof variant[number],
      "class": {
        "root": "has-data-[state=checked]:border-inverted/50 has-data-[state=checked]:bg-elevated"
      }
    },
    {
      "variant": "card" as typeof variant[number],
      "disabled": true,
      "class": {
        "root": "cursor-not-allowed"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-primary not-has-disabled:has-data-[state=checked]:border-primary"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-secondary not-has-disabled:has-data-[state=checked]:border-secondary"
      }
    },
    {
      "color": "success" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-success not-has-disabled:has-data-[state=checked]:border-success"
      }
    },
    {
      "color": "info" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-info not-has-disabled:has-data-[state=checked]:border-info"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-warning not-has-disabled:has-data-[state=checked]:border-warning"
      }
    },
    {
      "color": "error" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-error not-has-disabled:has-data-[state=checked]:border-error"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "indicator": "hidden" as typeof indicator[number],
      "highlight": true,
      "class": {
        "root": "not-has-disabled:border-inverted not-has-disabled:has-data-[state=checked]:border-inverted"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-primary"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-secondary"
      }
    },
    {
      "color": "success" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-success"
      }
    },
    {
      "color": "info" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-info"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-warning"
      }
    },
    {
      "color": "error" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-error"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "highlight": true,
      "class": {
        "base": "ring-inverted"
      }
    }
  ],
  "defaultVariants": {
    "highlight": false,
    "size": "md" as typeof size[number],
    "color": "primary" as typeof color[number],
    "variant": "list" as typeof variant[number],
    "indicator": "start" as typeof indicator[number]
  }
}