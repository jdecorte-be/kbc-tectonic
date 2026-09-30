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
  "outline",
  "soft",
  "subtle",
  "naked"
] as const

export default {
  "slots": {
    "root": "relative flex flex-col items-stretch gap-2 px-2.5 py-2 w-full rounded-lg backdrop-blur-sm",
    "header": "flex items-center gap-1.5",
    "body": "items-start gap-1.5",
    "footer": "flex items-center justify-between gap-1.5",
    "base": "px-0"
  },
  "variants": {
    "color": {
      "primary": "",
      "secondary": "",
      "success": "",
      "info": "",
      "warning": "",
      "error": "",
      "neutral": ""
    },
    "variant": {
      "outline": {
        "root": "bg-default/75 ring ring-default"
      },
      "soft": {
        "root": "bg-elevated/50"
      },
      "subtle": {
        "root": "bg-elevated/50 ring ring-default"
      },
      "naked": {
        "root": ""
      }
    }
  },
  "compoundVariants": [
    {
      "color": "primary" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-primary/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-primary has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-primary"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-secondary/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-secondary has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-secondary"
      }
    },
    {
      "color": "success" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-success/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-success has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-success"
      }
    },
    {
      "color": "info" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-info/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-info has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-info"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-warning/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-warning has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-warning"
      }
    },
    {
      "color": "error" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-error/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-error has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-error"
      }
    },
    {
      "color": "primary" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-primary/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    },
    {
      "color": "secondary" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-secondary/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    },
    {
      "color": "success" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-success/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    },
    {
      "color": "info" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-info/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    },
    {
      "color": "warning" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-warning/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    },
    {
      "color": "error" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-error/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "variant": [
        "outline" as typeof variant[number],
        "subtle" as typeof variant[number]
      ],
      "class": {
        "root": "outline-inverted/25 has-[textarea:focus-visible]:outline-3 has-[textarea:focus-visible]:ring-inverted has-[[contenteditable]:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:ring-inverted"
      }
    },
    {
      "color": "neutral" as typeof color[number],
      "variant": "soft" as typeof variant[number],
      "class": {
        "root": "outline-inverted/25 has-[textarea:focus-visible]:outline-3 has-[[contenteditable]:focus-visible]:outline-3"
      }
    }
  ],
  "defaultVariants": {
    "color": "primary" as typeof color[number],
    "variant": "outline" as typeof variant[number]
  }
}