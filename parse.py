import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
global order
from collections import defaultdict, Counter
import argparse

loc = []
comms = 0
labels = 0
jumps = 0
fwjumps = 0
backjumps = 0
badjumps = 0
declared_labels = []
used_labels = []

order = 1
root = ET.Element("program", language="IPPcode24")
# Regulární výrazy pro různé typy tokenů
def print_help():
    
    print("Usage: python3 main.py <input_file> <output_file>")

regex_patterns = {
    "VARIABLE": r"^(LF|TF|GF)@[a-zA-Z_][a-zA-Z0-9_$&%*!?-]*$",  # Citlivé na velikost písmen
    "CONSTANT": r"^(int@(-?0x[0-9a-fA-F]+|-?0o[0-7]+|-?\d+)|bool@(true|false)|string@([^\s#\\]|\\[0-9]{3})*|nil@nil)$",
 # Smíšená citlivost
    "INSTRUCTION": r"^[a-z]",  # Necitlivé na velikost písmen, použijeme re.IGNORECASE pro porovnání
    "LABEL": r"^[a-zA-Z_][a-zA-Z0-9_$&%*!?-]*$",
    "Comm" : r"^(#.*$)"
    
}


def get_type(word):
    return word.split("@")[0]
    

def create_token(token_type, value):
    return {"type": token_type, "value": value}


def identify_token(word):
    # Kontrola, zda je slovo proměnná nebo konstanta
    if re.match(regex_patterns["VARIABLE"], word):
        return create_token("VARIABLE", word)
    elif re.match(regex_patterns["CONSTANT"], word):
        return create_token("CONSTANT", word)
    # Kontrola, zda je slovo návěští (LABEL), mělo by mít stejný vzor jako VARIABLE
    elif re.match(regex_patterns["LABEL"], word):
        return create_token("LABEL", word)
    elif(re.match(regex_patterns["Comm"], word)):
        return create_token("Comm", word)
    elif word == ".IPPcode24":
        return create_token("Header", word)
    else:
        return create_token("UNKNOWN", word)

def variable_identify(instruction, word, arg_count):
    if re.match(regex_patterns["VARIABLE"], word["value"]):
        arg1 = ET.SubElement(instruction, "arg" +str(arg_count), type="var")
        arg1.text = word["value"]
    elif re.match(regex_patterns["CONSTANT"], word["value"]):
        arg_type = get_type(word["value"])
        pieces = word["value"].split("@", 1)
        #text = word["value"].split("@")[0]
        text = pieces[1]
        arg1 = ET.SubElement(instruction, "arg" + str(arg_count), type=arg_type)
        arg1.text = text

def add_argument(instruction, word, arg_count):
    arg1 = ET.SubElement(instruction, "arg" + str(arg_count), type="var")
    arg1.text = word["value"]
   
def variable_check(tokens):
    var = identify_token(tokens.pop(0))
    if var["type"] != "VARIABLE":
        sys.exit(23)
    return var   

def symbol_check(tokens):
    symb = identify_token(tokens.pop(0))
    if symb["type"] not in ["VARIABLE", "CONSTANT"]:
        print(symb["type"])
        sys.exit(23)
    return symb

def add_label(instruction, label, arg_count):
    global declared_labels
    global used_labels
    global fwjumps
    global backjumps
    arg1 = ET.SubElement(instruction, "arg" + str(arg_count), type="label")
    arg1.text = label["value"]
    if label["value"] in declared_labels:
        backjumps += 1
    else:
        used_labels.append(label["value"])
        fwjumps += 1
        

def parse_move(tokens):
    var = variable_check(tokens)
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="MOVE")
    add_argument(instruction, var,1)
    variable_identify(instruction, symb, 2)
    
    # Přidání argumentu pro symbol

def get_args():
    file_exist = False
    current_file = None
    stats_files = {}
    parser = argparse.ArgumentParser()
    parser.add_argument('--stats', metavar='file', action='append', help='Soubor pro statistiky a typy statistik.')
    parser.add_argument('--loc', action='store_true', help='Počet řádků s instrukcemi.')
    parser.add_argument('--comments', action='store_true', help='Počet komentářů.')
    parser.add_argument('--labels', action='store_true', help='Počet návěští.')
    parser.add_argument('--jumps', action='store_true', help='Počet skoků.')
    parser.add_argument('--fwjumps', action='store_true', help='Počet dopředných skoků.')
    parser.add_argument('--backjumps', action='store_true', help='Počet zpětných skoků.')
    parser.add_argument('--badjumps', action='store_true', help='Počet skoků na neexistující návěští.')
    parser.add_argument('--frequent', action='store_true', help='Nejčastější operační kódy.')
    parser.add_argument('--print', action='append', help='Výpis řetězce.')
    parser.add_argument('--eol', action='store_true', help='Vytiskne odřádkování.')
    args = parser.parse_known_args()
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith("--stats="):
            file_exist = True
            current_file = arg.split("=")[1]
            if current_file not in stats_files:
                stats_files[current_file] = []
        elif arg in stats or arg.startswith("--print="):
            if not file_exist:
                sys.exit(10)
            stats_files[current_file].append(arg)
        else:
            exit(1)

    for file, args in stats_files.items():
        with open(file, 'w') as f:
            for arg in args:
                if arg.startswith("--print="):
                    f.write(arg.split("=")[1] + "\n")
                    continue
                else:
                    output = stats[arg]()
                    f.write(f"{output}\n")
   
   
    
def parse_defvar(tokens):
    var = variable_check(tokens)
    
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="DEFVAR")
    add_argument(instruction, var, 1)

def parse_pushs(tokens):
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="PUSHS")
    variable_identify(instruction, symb, 1)
    
def parse_pops(tokens):
    var = identify_token(tokens.pop(0))
    if var["type"] != "VARIABLE":
        sys.exit("Expected variable, got " + var["value"])
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="POPS")
    add_argument(instruction, var,1)

def parse_arithmetic(tokens, opcode):
    var = variable_check(tokens)
    symb = symbol_check(tokens)
    if opcode != "NOT":
        symb1 = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode=opcode)
    add_argument(instruction, var,1)
    variable_identify(instruction, symb,2)
    if opcode != "NOT":
       variable_identify(instruction, symb1,3)

def add_instruction(opcode):
    
    ET.SubElement(root, "instruction", order=str(order), opcode=opcode)    

def parse_read(tokens):
    var = variable_check(tokens)
    type = identify_token(tokens.pop(0))
    if type["value"] not in ["int", "string", "bool"]:
        sys.exit(23)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="READ")
    add_argument(instruction, var, 1)
    arg2 = ET.SubElement(instruction, "arg2", type="type")
    arg2.text = type["value"]            

def parse_write(tokens):
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="WRITE")
    variable_identify(instruction, symb, 1)


def parse_strings(tokens, opcode):
    var = variable_check(tokens)
    symb = symbol_check(tokens)
    symb1 = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode=opcode)
    add_argument(instruction, var, 1)
    variable_identify(instruction, symb, 2)
    variable_identify(instruction, symb1, 3)


def parse_int2char(tokens):
    var = variable_check(tokens)
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="INT2CHAR")
    add_argument(instruction, var, 1)
    variable_identify(instruction, symb, 2)


def parse_strlen(tokens):
    var = variable_check(tokens)
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="STRLEN")
    add_argument(instruction, var, 1)
    variable_identify(instruction, symb, 2)
def parse_type(tokens):
    var = variable_check(tokens)
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="TYPE")
    add_argument(instruction, var, 1)
    variable_identify(instruction, symb, 2)

def parse_exit(tokens):
    symb = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode="EXIT")
    variable_identify(instruction, symb, 1)

stats = {
    "--loc" : lambda: f"{len(loc)}",
    "--comments" : lambda: f"{comms}",
    "--labels" : lambda: f"{labels}",
    "--jumps" : lambda: f"{jumps}",
    "--fwjumps" : lambda: f"{fwjumps}",
    "--backjumps" : lambda: f"{backjumps}",
    "--badjumps" : lambda: f"{badjumps}",
    "--frequent" : lambda: f"{frequency()}",
    "--eol" : lambda: f"\n",
    
    
        
}
instructions = {
    "MOVE": parse_move,
    "DEFVAR": parse_defvar,
    "PUSHS": parse_pushs,
    "POPS": parse_pops,
    "READ" : parse_read,
    "WRITE" : parse_write,
    "INT2CHAR" : parse_int2char,
    "STRLEN" : parse_strlen,
    "TYPE" : parse_type,
    "EXIT" : parse_exit
    # Další instrukce...
}


def parse_label(tokens, opcode, arg_count):
    global declared_labels
    global labels
    global backjumps
    global fwjumps
    global jumps
    global used_labels
    label = identify_token(tokens.pop(0))
    if label["type"] != "LABEL":
        sys.exit("Expected label, got " + label["value"])
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode=opcode)
    arg1 = ET.SubElement(instruction, "arg" + str(arg_count), type="label")
    arg1.text = label["value"]
    # if label["value"] in declared_labels:
    #     sys.exit(52)
    if opcode == "LABEL":
        declared_labels.append(label["value"])
        labels += 1
    else:
        if label["value"] in declared_labels:
            backjumps += 1
        else:
            used_labels.append(label["value"])
            fwjumps += 1
        jumps += 1

def frequency():
    
    
    
    opcode_counts = Counter(loc)
    most_freq = opcode_counts.most_common()
    return ','.join([op_code for op_code, count in most_freq])

def parse_jumps(tokens, opcode):
    global jumps
    label = identify_token(tokens.pop(0))
    if label["type"] != "LABEL":
        sys.exit("Expected label, got " + label["value"])
    symb1 = symbol_check(tokens)
    symb2 = symbol_check(tokens)
    instruction = ET.SubElement(root, "instruction", order=str(order), opcode=opcode)
    add_label(instruction, label, 1)
    variable_identify(instruction, symb1,2)
    variable_identify(instruction, symb2,3)
    jumps += 1


def main():
    label = ["LABEL", "JUMP", "CALL"]
    jumps = ["JUMPIFEQ", "JUMPIFNEQ"]
    strings = ["CONCAT", "GETCHAR", "SETCHAR"]
    arithemtic = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT","STRI2INT"]
    frames = ["PUSHFRAME", "CREATEFRAME", "POPFRAME","RETURN","BREAK"]
    global order
    global comms
    global loc
    global badjumps
    global labels
    order = 1
    
    tokens = []
    for line in sys.stdin:
        for i in line.split():
            if identify_token(i)["type"] == "Comm":
                comms += 1
        words_before = line.split('#')[0].strip()
        
        instruction_count = 0
        if words_before:
            words = words_before.split()
            # print("KOKOOOOOOOOOOOOOOOOT", words)
            for word in words:
                if any(word.upper() in lst for lst in [instructions, frames, arithemtic, strings, label, jumps]): # Only one instruction per line !
                    instruction_count += 1
                    loc.append(word.upper())
                if instruction_count == 2:
                    sys.exit(69)    # aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
                
            tokens.extend(words)
            

    if identify_token(tokens.pop(0))["value"] != ".IPPcode24":
        sys.exit(21)
        
        
    tree = ET.ElementTree(root)
    # DONT FORGET: NA JEDNEM RADKU MAX 1 INSTRUKCE !!!!!!!!!!!!!
    while tokens:
        token = identify_token(tokens.pop(0))
        # print(token["type"], token["value"])
        if token["value"].upper() in instructions:
            instructions[token["value"].upper()](tokens)
        elif token["value"].upper() in frames:
            add_instruction(token["value"])
        elif token["value"].upper() in arithemtic:
            parse_arithmetic(tokens, token["value"])
        elif token["value"].upper() in strings:
            parse_strings(tokens, token["value"])
        elif token["value"].upper() in label:
            parse_label(tokens, token["value"], 1)
        elif token["value"].upper() in jumps:
            parse_jumps(tokens, token["value"])
        elif token["type"] == "UNKNOWN":
            sys.exit("Unknown token: " + token["value"])
        elif token["type"] == "Comm":
            pass
        elif token["type"] == "Header":
            sys.exit(22)
        else:
            sys.exit("Unknown instruction: " + token["value"])
        order += 1

    args = get_args()
    ET.indent(tree, space="\t")
    tree.write(sys.stdout, encoding="unicode", xml_declaration=True)

    for i in used_labels:
        if i not in declared_labels:
            badjumps += 1
    
    
  
    
    # print("AAAAAAAAAA ->" , comms)
    # print("AAAAAAAAAA ->" , len(loc))
    # print("AAAAAAAAAA ->" , labels)
    # print("fwjump", fwjumps)
    # print("backjump", backjumps)
    # print("badjumps", badjumps)
    
    
    # print(i)
if __name__ == "__main__":
    
    main()
# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
