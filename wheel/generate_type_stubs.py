from pathlib import Path
from typing import Any, List, Optional, Tuple
from glob import glob

output_file = Path(__file__).parent.resolve() / "chia_rs.pyi"
input_dir = Path(__file__).parent.parent.resolve() / "chia-protocol" / "src"

# enums are exposed to python as int
enums = set(["NodeType", "ProtocolMessageTypes"])

def transform_type(m: str) -> str:
    n, t = m.split(":")
    if "List[" in t:
        t = t.replace("List[", "Sequence[")
    elif "bytes32" == t.strip():
        t = " bytes"
    elif t.strip() in enums:
        t = " int"
    return f"{n}:{t}"


def print_class(f: Any, name: str, members: List[str], extra: Optional[List[str]] = None):

    # f-strings don't allow backslashes, which makes it a bit tricky to
    # manipulate strings with newlines
    nl = "\n"
    extra_members = None
    if extra is not None:
        extra_members = ''.join(map(lambda x: '\n    ' + x, extra));

    f.write(
        f"""
class {name}:
    {(nl + '    ').join(members)}{extra_members if extra else ''}
    def __init__(
        self,
        {(',' + nl + '        ').join(map(transform_type, members))}
    ) -> None: ...
    def __hash__(self) -> int: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __richcmp__(self) -> Any: ...
    def __deepcopy__(self) -> {name}: ...
    def __copy__(self) -> {name}: ...
    @staticmethod
    def from_bytes(bytes) -> {name}: ...
    @staticmethod
    def parse_rust(ReadableBuffer) -> Tuple[{name}, int]: ...
    def to_bytes(self) -> bytes: ...
    def __bytes__(self) -> bytes: ...
    def get_hash(self) -> bytes32: ...
    def to_json_dict(self) -> Dict[str, Any]: ...
    @staticmethod
    def from_json_dict(o: Dict[str, Any]) -> {name}: ...
"""
    )


def rust_type_to_python(t: str) -> str:
    ret = (
        t.replace("<", "[")
        .replace(">", "]")
        .replace("Vec", "List")
        .replace("Option", "Optional")
        .replace("Bytes", "bytes")
        .replace("u8", "int")
        .replace("u16", "int")
        .replace("u32", "int")
        .replace("u64", "int")
        .replace("u128", "int")
        .replace("i8", "int")
        .replace("i16", "int")
        .replace("i32", "int")
        .replace("i64", "int")
        .replace("i128", "int")
        .strip()
    )
    if ret in enums:
        ret = "int"
    return ret


def parse_rust_source(filename: str) -> List[Tuple[str, List[str]]]:
    ret: List[Tuple[str], List[str]] = []
    in_struct: Optional[str] = None
    members: List[str] = []
    with open(filename) as f:
        for line in f:
            if not in_struct:
                if line.startswith("pub struct ") and "{" in line:
                    in_struct = line.split("pub struct ")[1].split("{")[0].strip()
                elif line.startswith("streamable_struct!") and "{" in line:
                    in_struct, line = line.split("(")[1].split("{")
                    in_struct = in_struct.strip()
                elif line.startswith("message_struct!") and "{" in line:
                    in_struct, line = line.split("(")[1].split("{")
                    in_struct = in_struct.strip()
                elif line.startswith("pub struct ") and "(" in line and ");" in line:
                    name = line.split("pub struct ")[1].split("(")[0].strip()
                    rust_args = line.split("(")[1].split(");")[0]
                    args = []
                    for idx, rust_type in enumerate(rust_args.split(",")):
                        py_type = rust_type_to_python(rust_type)
                        args.append(f"a{idx}: {py_type}")
                    ret.append((name, args))
                    continue
                else:
                    continue

            # we're parsing members
            # ignore macros
            if line.strip().startswith("#"):
                continue

            # a field
            if ":" in line:
                name, rust_type = line.split("//")[0].strip().split(":")
                # members are separated by , in rust. Strip that off
                try:
                    rust_type, line = rust_type.rsplit(",",1)
                except:
                    rust_type, line = rust_type.rsplit("}",1)
                    line = "}" + line
                py_type = rust_type_to_python(rust_type)
                members.append(f"{name}: {py_type}")

            # did we reach the end?
            if "}" in line:
                ret.append((in_struct, members))
                members = []
                in_struct = None
                continue


    assert in_struct is None
    return ret


extra_members = {"Coin": ["def name(self) -> bytes32: ..."]}

classes = []
for f in sorted(glob(str(input_dir / "*.rs"))):
    if f.endswith("bytes.rs"):
        continue
    classes.extend(parse_rust_source(f))

with open(output_file, "w") as f:
    f.write(
        """
#
# this file is generated by generate_type_stubs.py
#

from typing import List, Optional, Sequence, Tuple
from chia.types.blockchain_format.sized_bytes import bytes32

ReadableBuffer = Union[bytes, bytearray, memoryview]

def solution_generator(spends: Sequence[Tuple[Coin, bytes, bytes]]) -> bytes: ...
def solution_generator_backrefs(spends: Sequence[Tuple[Coin, bytes, bytes]]) -> bytes: ...

def compute_merkle_set_root(items: Sequence[bytes]) -> bytes: ...

def run_block_generator(
    program: ReadableBuffer, args: List[ReadableBuffer], max_cost: int, flags: int
) -> Tuple[Optional[int], Optional[SpendBundleConditions]]: ...

def run_block_generator2(
    program: ReadableBuffer, args: List[ReadableBuffer], max_cost: int, flags: int
) -> Tuple[Optional[int], Optional[SpendBundleConditions]]: ...

def run_puzzle(
    puzzle: bytes, solution: bytes, parent_id: bytes32, amount: int, max_cost: int, flags: int
) -> SpendBundleConditions: ...

COND_ARGS_NIL: int = ...
NO_UNKNOWN_CONDS: int = ...
STRICT_ARGS_COUNT: int = ...
LIMIT_ANNOUNCES: int = ...
AGG_SIG_ARGS: int = ...
LIMIT_HEAP: int = ...
ENABLE_ASSERT_BEFORE: int = ...
ENABLE_SOFTFORK_CONDITION: int = ...
MEMPOOL_MODE: int = ...
NO_RELATIVE_CONDITIONS_ON_EPHEMERAL: int = ...
ENABLE_BLS_OPS: int = ...
ENABLE_SECP_OPS: int = ...
ENABLE_BLS_OPS_OUTSIDE_GUARD: int = ...
LIMIT_OBJECTS: int = ...
ENABLE_FIXED_DIV: int = ...
ALLOW_BACKREFS: int = ...

ELIGIBLE_FOR_DEDUP: int = ...

NO_UNKNOWN_OPS: int = ...

def run_chia_program(
    program: bytes, args: bytes, max_cost: int, flags: int
) -> Pair[int, LazyNode]: ...

class LazyNode:
    def pair() -> Optional[Tuple[LazyNode, LazyNode]]: ...
    def atom() -> bytes: ...

def serialized_length(program: ReadableBuffer) -> int: ...
def tree_hash(program: ReadableBuffer) -> bytes32: ...
def get_puzzle_and_solution_for_coin(program: ReadableBuffer, args: ReadableBuffer, max_cost: int, find_parent: bytes32, find_amount: int, find_ph: bytes32, flags: int) -> Tuple[bytes, bytes]: ...
"""
    )

    print_class(f, "Spend",
        [
            "coin_id: bytes",
            "parent_id: bytes",
            "puzzle_hash: bytes",
            "coin_amount: int",
            "height_relative: Optional[int]",
            "seconds_relative: Optional[int]",
            "before_height_relative: Optional[int]",
            "before_seconds_relative: Optional[int]",
            "birth_height: Optional[int]",
            "birth_seconds: Optional[int]",
            "create_coin: List[Tuple[bytes, int, Optional[bytes]]]",
            "agg_sig_me: List[Tuple[bytes, bytes]]",
            "agg_sig_parent: List[Tuple[bytes, bytes]]",
            "agg_sig_puzzle: List[Tuple[bytes, bytes]]",
            "agg_sig_amount: List[Tuple[bytes, bytes]]",
            "agg_sig_puzzle_amount: List[Tuple[bytes, bytes]]",
            "agg_sig_parent_amount: List[Tuple[bytes, bytes]]",
            "agg_sig_parent_puzzle: List[Tuple[bytes, bytes]]",
            "flags: int",
        ],
    )

    print_class(f, "SpendBundleConditions",
        [
            "spends: List[Spend]",
            "reserve_fee: int",
            "height_absolute: int",
            "seconds_absolute: int",
            "before_height_absolute: Optional[int]",
            "before_seconds_absolute: Optional[int]",
            "agg_sig_unsafe: List[Tuple[bytes, bytes]]",
            "cost: int",
            "removal_amount: int",
            "addition_amount: int",
        ],
    )

    for c in classes:
        print_class(f, c[0], c[1], extra_members.get(c[0]))
