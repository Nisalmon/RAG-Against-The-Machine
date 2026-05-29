from src.classes import MinimalSource
from pathlib import Path
from typing import List, Dict
import json
import ast


def load_data() -> List[List[Dict[str, str]]]:
    data = [[], []]
    res = Path("vllm-0.10.1")
    for file in res.rglob("*"):
        if file.suffix != ".py" and file.suffix != ".md":
            continue
        tpe = 0 if file.suffix == ".py" else 1
        data[tpe].append({
            "path": str(file),
            "content": file.read_text(encoding="utf-8")
        })
    return data


def chunking(data):
    chunk_lst = []
    chunk_python(data[0], chunk_lst)
    chunk_markdown(data[1], chunk_lst)
    return chunk_lst



def chunk_python(data, lst):
    for elem in data:
        source = elem["content"]

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        lines = source.splitlines(keepends=True)

        line_starts = [0]
        for line in lines:
            line_starts.append(line_starts[-1] + len(line))

        for node in tree.body:
            if not isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                ),
            ):
                continue

            start = line_starts[node.lineno - 1]
            end = line_starts[node.end_lineno]

            lst.append(
                MinimalSource(
                    file_path=elem["path"],
                    first_character_index=start,
                    last_character_index=end,
                    text=elem["content"][start:end]
                )
            )


def chunk_markdown(data, lst):
    for elem in data:
        ind = 0
        fst_chr = ind
        nb_chr = 0
        previous_char = None
        for ch in elem["content"]:
            nb_chr += 1
            if (previous_char and previous_char == "\n" and ch == "\n") or nb_chr >= 2000:
                lst.append(
                    MinimalSource(
                        file_path=elem["path"],
                        first_character_index=fst_chr,
                        last_character_index=ind,
                        text=elem["content"][fst_chr:ind]
                    )
                )
                nb_chr = 0
                fst_chr = ind + 1
            previous_char = ch
            ind += 1
        lst.append(
                    MinimalSource(
                        file_path=elem["path"],
                        first_character_index=fst_chr,
                        last_character_index=len(elem["content"]),
                        text=elem["content"][fst_chr:ind]
                    )
                )


def store_processed_data(chunked_data):
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    serialized_data = [obj.__dict__ for obj in chunked_data]
    with open("./data/processed/processed_data.json", "w") as f:
        json.dump(serialized_data, fp=f,indent=4)


def main():
    data = load_data()
    chunked_data = chunking(data)
    store_processed_data(chunked_data)


if __name__ == "__main__":
    main()