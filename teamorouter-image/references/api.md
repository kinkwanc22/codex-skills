# TeamoRouter GPT Image 2.5 Sunburst API reference

Official documentation: https://teamorouter.cn/zh/docs/gpt-image-2.5-sunburst-api

## Endpoints

- Generate: `POST https://api.teamorouter.com/v1/images/generations` with JSON.
- Edit: `POST https://api.teamorouter.com/v1/images/edits` with multipart form data for image uploads.
- Authentication: `Authorization: Bearer <key>`.
- Model: `gpt-image-2.5-sunburst`; it must be explicit.

## Supported parameters

Generation supports `prompt`, `size`, `quality`, `n`, `output_format`, `output_compression`, `background`, `moderation`, `stream`, `partial_images`, and `user`.

Editing supports `image`, `mask`, `prompt`, `n`, `size`, `quality`, `background`, `input_fidelity`, `output_format`, `output_compression`, `stream`, `partial_images`, and `user`.

`moderation` accepts `auto` or `low`. `low` is a lower moderation strictness, not a documented way to disable safety review.

## Size validation

For a custom `WIDTHxHEIGHT`:

- width and height are multiples of 16;
- longest side is no more than 3840 pixels;
- aspect ratio is no more than 3:1;
- total pixels are from 655,360 through 8,294,400 inclusive.

Use pixel dimensions, not `1k`, `2k`, or `4k` strings.

## Billing boundary

Billing is per returned image and uses the actual longest side:

- up to 1024: 1K tier;
- up to 2048: 2K tier;
- above 2048: 4K tier.

With omitted or automatic size, the returned size determines the tier. This client defaults to an explicit `1024x1024` to make the request predictable; actual billing remains determined by the service response.
