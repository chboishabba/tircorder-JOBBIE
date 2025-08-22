# Visualiser Interface

Visualisers convert Python data structures into front-end output. The
`Visualiser.visualise(data)` method receives JSON serialisable data such as
nested `dict`, `list`, `int`, `float` and `str` values. Example payload:

```json
{
  "nodes": [{"id": 1, "label": "start"}],
  "edges": [[1, 2]]
}
```

## Bevy visualiser

`BevyVisualiser` serialises the payload to JSON and forwards it to a Bevy
application. The transport layer is left as a placeholder for now.

## Extending

To add another visualiser, subclass `Visualiser` and implement
`visualise(data)` with the desired output logic.
