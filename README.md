# Verbify
A web app for reviewing English irregular verbs

## Usage
Verbify runs entirely in your browser with Brython 3.15.0. It does not need an account, a database, or a backend; quiz answers are not saved or sent anywhere.

Start a local web server from the project root:

```sh
python -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000). Select the first and last verbs to review, enter the base form, past simple, and past participle for each prompt, and see your mastered-verb score and percentage at the end. The quiz logic is written in [python/main.py](./python/main.py); Brython and its standard library are loaded from jsDelivr.

## License
Thise project is licensed under the **MIT License**. See [LICENSE](./LICENSE) for more informations.
