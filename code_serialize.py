
import os
import pickle
import sys

import phply.phplex
import phply.phpparse

import file_system


def is_php_ast_struct(php_ast_node) :
    php_ast_node_class = str(php_ast_node.__class__)
    class_flag_offset = php_ast_node_class.find('phply.phpast.')
    
    if not -1 == class_flag_offset and not 'inlinehtml' == get_php_ast_struct_type(php_ast_node) :
        return True
    
    return False


def is_php_class_declare(php_ast_node):
    struct_type = get_php_ast_struct_type(php_ast_node)

    if 'class' == struct_type :
        return True

    return False

def is_php_function_declare(php_ast_node) :
    struct_type = get_php_ast_struct_type(php_ast_node)
    
    if 'function' == struct_type or 'method' == struct_type :
        return True
    
    return False

def is_php_function_call(php_ast_node) :
    struct_type = get_php_ast_struct_type(php_ast_node)
    
    if 'functioncall' == struct_type or 'methodcall' == struct_type or 'staticmethodcall' == struct_type :
        return True
        
    return False
        
def is_php_eval_call(php_ast_node) :
    if 'eval' == get_php_ast_struct_type(php_ast_node) :
        return True
        
    return False
        
def is_php_class(php_object_name) :
    if php_object_name.startswith('class$$') :
        return True
    
    return False

def is_php_number(php_value) :
    php_value_type = type(php_value)
    
    if int == php_value_type or float == php_value_type :
        return True
    
    return False

def is_php_string(php_value) :
    if str == type(php_value) :
        if '\'' == php_value[0] and '\'' == php_value[-1] :
            return True
        
    return False
    
def is_php_variant(php_value) :
    if str == type(php_value) :
        if '$' == php_value[0] :
            return True
        
    return False

def is_php_function(php_name):
    php_value_type = type(php_name)

    if str == php_value_type :
        if not -1 == php_name.find('()') :
            return True

    return False

def get_php_ast_struct_type(php_ast_node) :
    php_ast_node_class = str(php_ast_node.__class__)
    class_flag_offset = php_ast_node_class.find('phply.phpast.')
    class_flag_length = len('phply.phpast.')
    
    if not -1 == class_flag_offset :
        php_ast_node_type = php_ast_node_class[class_flag_offset + class_flag_length : -2].lower()
        
        return php_ast_node_type
        
    return False

def make_string(make_length,char = ' ') :
    output_string = ''
    
    for make_index in range(make_length) :
        output_string += char
        
    return output_string

def debug_output(php_ast,print_indent = 0) :
    for ast_index in php_ast :
        php_ast_struct_type = get_php_ast_struct_type(ast_index)
        
        if php_ast_struct_type :
            if 'if' == php_ast_struct_type :
                if ast_index.node :
                    print make_string(print_indent) + str(ast_index.lineno) + ' : if' , ast_index.expr
                    
                    if 1 < len(ast_index.node.nodes) :
                        debug_output(ast_index.node.nodes,print_indent + 2)
                    else :
                        debug_output([ast_index.node.nodes],print_indent + 2)
                if ast_index.elseifs :
                    print make_string(print_indent) + str(ast_index.lineno) + ' : else if' , ast_index.expr
                    
                    if 1 < len(ast_index.elseifs.node.nodes) :
                        debug_output(ast_index.elseifs.node.nodes,print_indent + 2)
                    else :
                        debug_output([ast_index.elseifs.node.nodes],print_indent + 2)
                if ast_index.else_ :
                    print make_string(print_indent) + str(ast_index.lineno) + ' : else' , ast_index.expr
                    
                    if 1 < len(ast_index.else_.node.nodes) :
                        debug_output(ast_index.else_.node.nodes,print_indent + 2)
                    else :
                        debug_output([ast_index.else_.node.nodes],print_indent + 2)
            else :
                ast_index_subdata = ''
                
                for ast_fields in ast_index.fields :
                    ast_index_subdata += str(ast_index.__getattribute__(ast_fields)) + ' '
                
                print make_string(print_indent) + str(ast_index.lineno) + ' : ' + php_ast_struct_type + ' ' + ast_index_subdata

def convert_ast(file_path) :
    if os.path.isfile(file_path) :
        php_code = file_system.read_file(file_path)
        php_ast = phply.phpparse.make_parser().parse(php_code,lexer = phply.phplex.lexer.clone())
        
        return php_ast
    
    return False

def get_value_reference(function_ast) :
    parament = function_ast
    result = ''
    
    if is_php_ast_struct(parament) :
        struct_type = get_php_ast_struct_type(parament)

        if 'arrayoffset' == struct_type :
            array_node = parament.node
            variant_name = ''
            array_index = ''
            
            if 'arrayoffset' == get_php_ast_struct_type(array_node) :
                array_index = parament.expr
                last_array_index = array_node.expr
                array_node_ = array_node.node
                
                if 'arrayoffset' == get_php_ast_struct_type(array_node_) :  # three level resolve ..
                    last_last_array_index = array_node_.expr
                    variant_name = array_node_.node.name
                    array_node__ = array_node_.node
                    
                    if 'arrayoffset' == get_php_ast_struct_type(array_node__) :
                        return result
                    
                    result = (variant_name,last_last_array_index,last_array_index,array_index)
                else :
                    variant_name = array_node.node.name
                    
                result = (variant_name,last_array_index,array_index)
            else :
                variant_name = parament.node.name
                array_index  = parament.expr
                
                result = (variant_name,array_index)
        elif 'variable' == struct_type :
            result = parament.name
        elif 'functioncall' == struct_type :
            function_name = parament.name + '()'
            function_arguments  = get_function_argument_list(parament)

            result = (function_name,function_arguments)
        else :
            result = str(parament)
            result = result[result.find('(') + 1 : result.rfind(')')]
    else :
        if str == type(parament) :
            result = '\'' + parament + '\''
        else :  #  is number ..
            result = str(parament)
    
    return result

def get_function_argument_list(function_ast) :
    if is_php_function_declare(function_ast) or is_php_function_call(function_ast) :
        function_argument_list = []
        
        for function_parament_index in function_ast.params :
            if None == function_parament_index :
                break
            
            if 'parameter' == get_php_ast_struct_type(function_parament_index) :
                parament = get_value_reference(function_parament_index.node)
                
                function_argument_list.append(parament)
            elif 'formalparameter' == get_php_ast_struct_type(function_parament_index) :
                function_argument_list.append(function_parament_index.name)
            
        return function_argument_list
    elif is_php_eval_call(function_ast) :
        return [get_value_reference(function_ast.expr)]
    
    return []

def get_assignment(assigenment_ast) :  #  WARNING !! I had ignore mutil-value calculate xref ..
    struct_type = get_php_ast_struct_type(assigenment_ast)

    if 'assignment' == struct_type :
        left = None
        right = None
        
        if 'name' in assigenment_ast.node.fields :  #  TIPS : this is a varaint ..
            left = assigenment_ast.node.name
        else :
            left = get_value_reference(assigenment_ast)  #  may is a $_array['sss'] ..
        
        if is_php_function_call(assigenment_ast.expr) :
            right = assigenment_ast.expr
        elif 'binaryop' == get_php_ast_struct_type(assigenment_ast.expr) :  #  mutil value calculate ..
            pass
        else :
            if str == type(assigenment_ast.expr) :
                right = assigenment_ast.expr
            else :
                right = get_value_reference(assigenment_ast.expr)

        return {
            'left' : left ,
            'right' : right
        }
    elif 'functioncall' == struct_type :  #  WARNING !! no support function ..
        pass

    return False

def get_syntax_argument_list(syntax_ast) :
    if not is_php_ast_struct(syntax_ast) :
        return False
    
    if 'expr' in syntax_ast.fields :
        syntax_argument_list = []
        
        if is_php_function_call(syntax_ast) :
            syntax_argument_list.append(get_function_argument_list(syntax_ast.nodes))
        else :
            syntax_argument_list.append(get_value_reference(syntax_ast.expr))
            
        return syntax_argument_list
    
    return False

def build_ast_index(php_ast) :
    if not len(php_ast) :
        return False
    
    def function_call_recursion(php_ast,current_function_name = '__global',current_function_argument_list = []) :
        sub_function_call = []
        current_function_call = []
        
        for php_ast_index in php_ast :
            ast_struct_type = get_php_ast_struct_type(php_ast_index)

            if 'function' == ast_struct_type or 'method' == ast_struct_type or 'class' == ast_struct_type :  #  new function or class ..
                function_name = php_ast_index.name

                if 'class' == ast_struct_type :  #  setting a flag for identification class name ..
                    function_name = 'class$$' + function_name

                function_argument_list = get_function_argument_list(php_ast_index)
                sub_function = function_call_recursion(php_ast_index.nodes,function_name,function_argument_list)
                
                sub_function_call.append(sub_function)
            elif 'functioncall' == ast_struct_type or 'methodcall' == ast_struct_type :  #  call function ..
                current_function_call.append({
                    'function_name' : php_ast_index.name ,
                    'function_argument' : get_function_argument_list(php_ast_index) ,
                    'line' : php_ast_index.lineno
                })
            elif 'eval' == ast_struct_type :  #  call eval ..
                current_function_call.append({
                    'function_name' : 'eval' ,
                    'function_argument' : get_function_argument_list(php_ast_index) ,
                    'line' : php_ast_index.lineno
                })
            else :  #  maybe some internal syntax will call function such like : echo system('pause') ..
                if not is_php_ast_struct(php_ast_index) :
                    continue
                
                for php_ast_index_sub_node_index in php_ast_index.fields :  #  list all attribute support fields ..
                    sub_ast_node = php_ast_index.__getattribute__(php_ast_index_sub_node_index)
                    sub_block = None
                    
                    if is_php_ast_struct(sub_ast_node) :
                        sub_ast = None
                        
                        try :
                            if 'node' in dir(sub_ast_node) and 'node' in sub_ast_node.fields :
                                if not 'nodes' in sub_ast_node.node.fields :
                                    continue

                                sub_ast = sub_ast_node.node.nodes
                            elif 'nodes' in dir(sub_ast_node) and 'nodes' in sub_ast_node.fields :
                                sub_ast = sub_ast_node.nodes
                            else :
                                continue
                        except :
                            continue
                        
                        sub_block = function_call_recursion(sub_ast,current_function_name,current_function_argument_list)
                    elif list == type(sub_ast_node) and len(sub_ast_node) :
                        sub_block = function_call_recursion(sub_ast_node,current_function_name,current_function_argument_list)
                    
                    if not None == sub_block :
                        for sub_block_call_index in sub_block['function_call'] :
                            current_function_call.append({
                                'function_name' : sub_block_call_index['function_name'] ,
                                'function_argument' : sub_block_call_index['function_argument'] ,
                                'line' : sub_block_call_index['line']
                            })
            
        return {
            'function' : current_function_name ,
            'function_argument' : current_function_argument_list ,
            'function_call' : current_function_call ,   #  search these direct reference point
            'subfunction_list' : sub_function_call      #  search these reference function
        }
    
    return function_call_recursion(php_ast)
    
def get_code(file_ast,file_line) :  #  get code from ast by line ..
    if not list == type(file_line) :
        file_line = [file_line]
    
    def node_loop(node_ast,file_line) :
        node_struct = []
        
        for node_index in node_ast :
            if not is_php_ast_struct(node_index) :
                continue

            if node_index.lineno in file_line :
                expression = get_function_argument_list(node_index)

                if False == expression :
                    expression = get_syntax_argument_list(node_index)

                    if False == expression :
                        expression = []
                else :  #  function call or declare ..
                    expression = [node_index.name] + expression
                
                node_struct.append({
                    'syntax' : get_php_ast_struct_type(node_index) ,
                    'expression' : expression ,
                    'line' : node_index.lineno
                })
                file_line.remove(node_index.lineno)
                
            sub_node_ast = None
                
            if 'node' in dir(node_index) and 'node' in node_index.fields :
                if not 'nodes' in node_index.node.fields :
                    continue
                    
                sub_node_ast = node_index.node.nodes
            elif 'nodes' in dir(node_index) and 'nodes' in node_index.fields :
                sub_node_ast = node_index.nodes
            else :
                continue
                
            node_struct += node_loop(sub_node_ast,file_line)
            
        return node_struct
    
    return node_loop(file_ast,file_line)

def get_function_argument(file_ast,function_name):

    def node_loop(node_ast,function_name) :
        result = []

        for node_index in node_ast :
            if not is_php_ast_struct(node_index) :
                continue

            if is_php_function_declare(node_index) :
                if function_name == node_index.name :
                    return get_function_argument_list(node_index) , node_index.lineno

            if is_php_class_declare(node_index) :
                function_arguments = get_function_argument(node_index.nodes,function_name)

                if function_arguments :
                    return function_arguments

            sub_node_ast = None

            try :
                if 'node' in dir(node_index) and 'node' in node_index.fields :
                    if not 'nodes' in node_index.node.fields:
                        continue

                    sub_node_ast = node_index.node.nodes
                elif 'nodes' in dir(node_index) and 'nodes' in node_index.fields :
                    sub_node_ast = node_index.nodes
                else:
                    continue
            except :
                continue

            result = node_loop(sub_node_ast, function_name)

            if result:
                break

        return result

    return node_loop(file_ast,function_name)

def get_function_code(file_ast,function_name) :
    
    def node_loop(node_ast,function_name) :
        result = False
        
        for node_index in node_ast :
            if not is_php_ast_struct(node_index) :
                continue
                
            if is_php_function_declare(node_index) :
                if function_name == node_index.name :
                    return node_index.nodes
                
            sub_node_ast = None
                
            try :
                if 'node' in dir(node_index) and 'node' in node_index.fields :
                    if not 'nodes' in node_index.node.fields :
                        continue

                    sub_node_ast = node_index.node.nodes
                elif 'nodes' in dir(node_index) and 'nodes' in node_index.fields :
                    sub_node_ast = node_index.nodes
                else :
                    continue
            except :
                continue
                
            result = node_loop(sub_node_ast,function_name)
            
            if result :
                break
                
        return result
            
    return node_loop(file_ast,function_name)
   
def cut_ast(function_code_ast,cut_to_line) :
    
    def node_loop(node_ast,cut_to_line) :
        code_list = []
        
        for node_index in node_ast :
            if not is_php_ast_struct(node_index) :
                continue
            
            if node_index.lineno <= cut_to_line :
                code_list.append({
                    'ast_code' : node_index ,
                    'line' : node_index.lineno
                })

            if node_index.lineno >= cut_to_line :
                return code_list
            
            sub_node_ast = None
                
            try :
                if 'node' in dir(node_index) and 'node' in node_index.fields :
                    if not 'nodes' in node_index.node.fields :
                        continue

                    sub_node_ast = node_index.node.nodes
                elif 'nodes' in dir(node_index) and 'nodes' in node_index.fields :
                    sub_node_ast = node_index.nodes
                else :
                    continue
            except :
                continue
                
            code_list += node_loop(sub_node_ast,cut_to_line)
            
        return code_list
    
    return node_loop(function_code_ast,cut_to_line)
    
def serialize(file_path) :
    if os.path.isfile(file_path) :
        ast = convert_ast(file_path)
        ast_quick_index = build_ast_index(ast)
        python_serialize_ast = pickle.dumps(ast)
        python_serialize_ast_quick_index = pickle.dumps(ast_quick_index)
        
        file_system.write_file(file_path + '.ast',python_serialize_ast)
        file_system.write_file(file_path + '.ast_index',python_serialize_ast_quick_index)
        
        return True
    elif os.path.isdir(file_path) :
        for dir_index in os.walk(file_path) :
            dir_path = dir_index[0] + file_system.get_system_directory_separator()
            
            for dir_file_index in dir_index[2] :
                dir_file_path = dir_path + dir_file_index
                ast = convert_ast(dir_file_path)
                ast_quick_index = build_ast_index(ast)
                python_serialize_ast = pickle.dumps(ast)
                python_serialize_ast_quick_index = pickle.dumps(ast_quick_index)

                file_system.write_file(dir_file_path + '.ast',python_serialize_ast)
                file_system.write_file(dir_file_path + '.ast_index',python_serialize_ast_quick_index)
    
        return True
    
    return False


if __name__ == '__main__' :
    if 2 == len(sys.argv) :
        '''
        php_ast = convert_ast(sys.argv[1])
        
        debug_output(php_ast)
        
        print ' '
        
        print build_ast_index(php_ast)
        '''

        php_ast = convert_ast(sys.argv[1])

        print get_code(php_ast,36)
        print get_assignment(get_code(php_ast,36)[0])
        
        shutdown_function_code = get_function_code(php_ast,'try_call_test')
        
        print shutdown_function_code
        
        print cut_ast(shutdown_function_code,29)
