# Dummy implementation 

This is an example implementation of a Kalavai template. Use it to bootstrap the development of your new template.

## External references

None

## How to use

```bash
kalavai job defaults dummy > values.yaml
kalavai job run dummy --value-path values.yam
```

Then monitor:
```bash
kalavai job list
```

Finally, stop:
```bash
kalavai job delete kalavai-dummy-template
```
