const loadingAnimation = [
  "carousel",
  "carousel-inverse",
  "swing",
  "elastic"
] as const

const loadingColor = [
  "primary",
  "secondary",
  "success",
  "info",
  "warning",
  "error",
  "neutral"
] as const

export default {
  "slots": {
    "root": "relative overflow-auto outline-primary/25 focus-visible:outline-3",
    "base": "min-w-full overflow-clip",
    "caption": "sr-only",
    "thead": "relative",
    "tbody": "isolate [&>tr]:data-[selectable=true]:hover:bg-elevated/50 [&>tr]:data-[selectable=true]:outline-primary/25 [&>tr]:data-[selectable=true]:focus-visible:outline-3 [&>tr]:data-[selectable=true]:-outline-offset-3 divide-y divide-default",
    "tfoot": "relative",
    "tr": "data-[selected=true]:bg-elevated/50",
    "th": "px-4 py-3.5 text-sm text-highlighted text-start font-semibold [&:has([role=checkbox])]:pe-0",
    "td": "p-4 text-sm text-muted whitespace-nowrap [&:has([role=checkbox])]:pe-0",
    "separator": "absolute z-1 start-0 w-full h-px bg-(--ui-border-accented)",
    "empty": "py-6 text-center text-sm text-muted",
    "loading": "py-6 text-center"
  },
  "variants": {
    "pinned": {
      "true": {
        "th": "sticky bg-default/75 z-1",
        "td": "sticky bg-default/75 z-1"
      }
    },
    "sticky": {
      "true": {
        "thead": "sticky top-0 inset-x-0 bg-default/75 backdrop-blur-sm z-1",
        "tfoot": "sticky bottom-0 inset-x-0 bg-default/75 backdrop-blur-sm z-1"
      },
      "header": {
        "thead": "sticky top-0 inset-x-0 bg-default/75 backdrop-blur-sm z-1"
      },
      "footer": {
        "tfoot": "sticky bottom-0 inset-x-0 bg-default/75 backdrop-blur-sm z-1"
      }
    },
    "loading": {
      "true": {
        "thead": "after:absolute after:z-1 after:h-px motion-reduce:after:inset-x-0 motion-reduce:after:animate-pulse"
      }
    },
    "externalScroll": {
      "true": {
        "root": "overflow-visible"
      }
    },
    "loadingAnimation": {
      "carousel": "",
      "carousel-inverse": "",
      "swing": "",
      "elastic": ""
    },
    "loadingColor": {
      "primary": "",
      "secondary": "",
      "success": "",
      "info": "",
      "warning": "",
      "error": "",
      "neutral": ""
    }
  },
  "compoundVariants": [
    {
      "loading": true,
      "loadingColor": "primary" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-primary"
      }
    },
    {
      "loading": true,
      "loadingColor": "secondary" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-secondary"
      }
    },
    {
      "loading": true,
      "loadingColor": "success" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-success"
      }
    },
    {
      "loading": true,
      "loadingColor": "info" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-info"
      }
    },
    {
      "loading": true,
      "loadingColor": "warning" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-warning"
      }
    },
    {
      "loading": true,
      "loadingColor": "error" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-error"
      }
    },
    {
      "loading": true,
      "loadingColor": "neutral" as typeof loadingColor[number],
      "class": {
        "thead": "after:bg-inverted"
      }
    },
    {
      "loading": true,
      "loadingAnimation": "carousel" as typeof loadingAnimation[number],
      "class": {
        "thead": "motion-safe:after:animate-[carousel_2s_linear_infinite] motion-safe:rtl:after:animate-[carousel-rtl_2s_linear_infinite]"
      }
    },
    {
      "loading": true,
      "loadingAnimation": "carousel-inverse" as typeof loadingAnimation[number],
      "class": {
        "thead": "motion-safe:after:animate-[carousel-inverse_2s_linear_infinite] motion-safe:rtl:after:animate-[carousel-inverse-rtl_2s_linear_infinite]"
      }
    },
    {
      "loading": true,
      "loadingAnimation": "swing" as typeof loadingAnimation[number],
      "class": {
        "thead": "motion-safe:after:animate-[swing_2s_var(--ease-in-out)_infinite]"
      }
    },
    {
      "loading": true,
      "loadingAnimation": "elastic" as typeof loadingAnimation[number],
      "class": {
        "thead": "motion-safe:after:animate-[elastic_2s_var(--ease-in-out)_infinite]"
      }
    }
  ],
  "defaultVariants": {
    "loadingColor": "primary" as typeof loadingColor[number],
    "loadingAnimation": "carousel" as typeof loadingAnimation[number]
  }
}