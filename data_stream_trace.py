
# coding:utf-8

import code_serialize
import source_trace


def pick_file_ast(file_ast,speacial_file_path) :
    file_ast_ = None
    file_ast_quick_index_ = None

    for file_ast_index in file_ast['file_ast_list'] :
        if file_ast_index['file_path'] == speacial_file_path :
            file_ast_ = file_ast_index['file_ast']

            break

    for file_ast_quick_index in file_ast['file_ast_quick_index_list'] :
        if file_ast_quick_index['file_path'] == speacial_file_path :
            file_ast_quick_index_ = file_ast_quick_index['file_ast']

            break

    if not None == file_ast_ and not None == file_ast_quick_index_ :
        return {
            'file_ast' : file_ast_ ,
            'file_ast_quick_index' : file_ast_quick_index_ ,
            'file_name' : speacial_file_path
        }

    return False

def is_controlled_value(ast_node_value) :
    if ast_node_value.startswith('$') :
        return True

    return False

def get_controlled_argument_list(ast_node_argument_list) :
    if not len(ast_node_argument_list) :
        return False

    controlled_argument_list = []
    argument_index = -1
    
    for ast_node_argument_index in ast_node_argument_list :
        argument_index += 1

        if tuple == type (ast_node_argument_index) :  #  TIPS : it is array index reference ..
            if not is_controlled_value(ast_node_argument_index[0]) :
                continue
        else :
            if not is_controlled_value(ast_node_argument_index) :
                continue

        controlled_argument_list.append(argument_index)

    return controlled_argument_list

def function_inside_data_stream_trace(file_ast,valid_trace_strategy,function_name,code_location,trace_point_list) :
    function_argument = []
    
    if code_location.has_key('syntax') :  #  TIPS : it is a syntax tag ..
        function_argument = code_location['syntax_argument']
    else :
        function_argument = code_location['function_argument']

    controlled_argument_list = get_controlled_argument_list(function_argument)

    #  TIPS : we need target on trace function call when trace_point_list is None ..
    if not controlled_argument_list :
        return False

    real_trace_point_list = []

    for controlled_argument_index in controlled_argument_list :  #  search real controlled and trace point ..
        if controlled_argument_index in trace_point_list :
            real_trace_point_list.append(controlled_argument_index)

    if not len(real_trace_point_list) :
        return False

    first_trace_name_list = []

    for function_argument_index in range(len(function_argument)) :  #  search these controlled variant name ..
        if function_argument_index in real_trace_point_list :
            first_trace_name_list.append(function_argument[function_argument_index])

    function_argument , function_declare_line = code_serialize.get_function_argument(file_ast,function_name)
    function_code = code_serialize.get_function_code(file_ast,function_name)
    function_search_code = code_serialize.cut_ast(function_code,code_location)

    if not len(function_search_code) :  #  maybe this code_location is error ..
        return False

    def xref_trace(function_search_code,valid_trace_strategy,trace_name) :  #  find data stream trace ..
        trace_name_list = []

        for function_search_code_index in reversed(range(len(function_search_code))) :
            code = function_search_code[function_search_code_index]
            code_assignment = code_serialize.get_assignment(code['ast_code'])

            if not code_assignment :
                continue

            code_assignment_left = code_assignment['left']
            code_assignment_right = code_assignment['right']

            if not trace_name == code_assignment_left :
                continue

            next_trace_name_list = []

            if code_serialize.is_php_function_call(code_assignment_right) :
                function_name = code_assignment_right.name
                function_argument_list = code_serialize.get_function_argument_list(code_assignment_right)
                no_search = False

                for valid_trace_strategy_index in valid_trace_strategy :  #  Checking data is user controlled by strategy ..
                    if not 'function' == valid_trace_strategy_index['struct'] :
                        continue

                    if function_name == valid_trace_strategy_index['function'] :
                        trace_name_list.append([{
                            'line' : code['line'] ,
                            'name' : code_assignment_right ,
                        }])

                        no_search = True

                        break

                if no_search :
                    pass

                #  WARNING !!! it need xref for function trace ..
                #  trace function ..
            else :
                code_assignment_right_variant = None
                code_assignment_right_array_index = None

                if tuple == type(code_assignment_right) :  #  is Array ..
                    if code_serialize.is_php_variant(code_assignment_right[0]) :
                        code_assignment_right_variant = code_assignment_right[0]
                        code_assignment_right_array_index = code_assignment_right[1]
                    else :
                        continue
                elif code_serialize.is_php_variant(code_assignment_right) :
                    code_assignment_right_variant = code_assignment_right
                else :
                    continue

                no_search = False

                for valid_trace_strategy_index in valid_trace_strategy :  #  Checking data is user controlled by strategy ..
                    if not 'variant' == valid_trace_strategy_index['struct'] :
                        continue

                    if code_assignment_right_variant == valid_trace_strategy_index['variant'] :
                        trace_name_list.append([{
                            'line' : code['line'] ,
                            'name' : code_assignment_right ,
                        }])

                        no_search = True

                        break

                if no_search :
                    break

                if not function_search_code_index :  #  trace variant ..
                    next_trace_name_list = xref_trace([function_search_code[0]],valid_trace_strategy,code_assignment_right)
                else :
                    next_trace_name_list = xref_trace(function_search_code[ : function_search_code_index],valid_trace_strategy,code_assignment_right)

                for next_trace_name_index in next_trace_name_list :
                    trace_name_list.append([{
                                                'line' : code['line'] ,
                                                'name' : trace_name
                                            }] + next_trace_name_index)

        if len(trace_name_list) :
            return trace_name_list

        return [[{
            'line' : function_search_code[-1]['line'] ,
            'name' : trace_name
        }]]

    trace_link_list = []

    for trace_name_index in first_trace_name_list :
        trace_record = xref_trace(function_search_code,valid_trace_strategy,trace_name_index)

        if not len(trace_record) :  #  no found trace link ..
            continue

        for trace_record_index in trace_record :
            if not len(trace_record_index) :
                continue

            last_trace_record_index = trace_record_index[-1]['name']
            last_trace_record_index_name = None
            last_trace_record_index_index = None

            if tuple == type(last_trace_record_index) :  #  is Array ..
                last_trace_record_index_name = last_trace_record_index[0]
                last_trace_record_index_index = last_trace_record_index[1]
            else :
                last_trace_record_index_name = last_trace_record_index

            is_trace_into_function_arguments = True

            for valid_trace_strategy_index in valid_trace_strategy :  #  Checking data is user controlled by strategy ..
                if 'function' == valid_trace_strategy_index['struct'] :
                    if last_trace_record_index_name == valid_trace_strategy_index['function'] :
                        trace_link_list += trace_record
                        is_trace_into_function_arguments = False
                elif 'variant' == valid_trace_strategy_index['struct'] :
                    if last_trace_record_index_name == valid_trace_strategy_index['variant'] :
                        trace_link_list += trace_record
                        is_trace_into_function_arguments = False

            if is_trace_into_function_arguments :
                if last_trace_record_index_name in function_argument :  #  it is valid trace record ..
                    trace_link_list += trace_record

    return trace_link_list

def source_trace_data_stream_link(file_ast,source_strategy,valid_trace_strategy,source_trace_record) :  #  search valid trace path ..
    trace_link = []

    if not len(source_trace_record) :
        return trace_link

    if dict == type(source_trace_record) :
        source_trace_record = [source_trace_record]

    for sub_function_index in source_trace_record :
        function_name = sub_function_index['function']

        if code_serialize.is_php_class(function_name) :
            class_function_search_result = source_trace_data_stream_link(file_ast,source_strategy,valid_trace_strategy,sub_function_index['subfunction_call'])

            trace_link += class_function_search_result
        else :
            function_argument ,function_declare_line = code_serialize.get_function_argument(file_ast['file_ast'],function_name)
            reference_function = sub_function_index['reference_function']
            reference_point = sub_function_index['reference_point']
            current_function_trace_link = []
            is_trace_into_valid_strategy = False

            for function_call_index in sub_function_index['function_call'] :  #  first time we need to search this link in current function ..
                search_strategy = False

                if function_call_index.has_key('syntax') :
                    search_strategy = source_trace.get_source_trace_strategy_by_syntax(source_strategy,function_call_index['syntax'])
                elif function_call_index.has_key('function_name') :
                    search_strategy = source_trace.get_source_trace_strategy_by_function(source_strategy,function_call_index['function_name'])

                if not search_strategy :
                    continue

                trace_record = function_inside_data_stream_trace(file_ast['file_ast'],valid_trace_strategy,function_name,function_call_index,search_strategy['trace_point'])
                valid_trace_record = []

                if not trace_record :  #  this trace link is invalid ..
                    continue

                for trace_record_index in trace_record :  #  check invalid value ..
                    is_current_trace_record_valid = False

                    if len(trace_record_index) :
                        last_trace_record = trace_record_index[-1]
                        last_trace_record_name = None
                        last_trace_record_array_index = None

                        if tuple == type(last_trace_record['name']) :
                            last_trace_record_name = last_trace_record['name'][0]
                            last_trace_record_array_index = last_trace_record['name'][1]
                        else :
                            last_trace_record_name = last_trace_record['name']

                        if code_serialize.is_php_variant(last_trace_record_name) :  #  name is not a variant and it is invalid variant ..
                            is_current_trace_record_valid = True

                    if is_current_trace_record_valid :
                        valid_trace_record.append(trace_record_index)

                current_function_trace_link += valid_trace_record

            next_function_trace_point_list = []

            for current_function_trace_index in current_function_trace_link :  #  find next function call arguments trace point ..
                if not len(current_function_trace_index) :
                    continue

                last_trace_record = current_function_trace_index[-1]
                last_trace_record_name = None
                last_trace_record_array_index = None

                if tuple == type(last_trace_record['name']) :
                    last_trace_record_name = last_trace_record['name'][0]
                    last_trace_record_array_index = last_trace_record['name'][1]
                else :
                    last_trace_record_name = last_trace_record['name']

                for valid_trace_strategy_index in valid_trace_strategy :  #  Checking data is user controlled by strategy ..
                    if 'function' == valid_trace_strategy_index['struct'] :
                        if last_trace_record_name == valid_trace_strategy_index['function'] :
                            trace_link.append({
                                'file_name' : file_ast['file_name'] ,
                                'function' : function_name ,
                                'sub_function_trace' : [] ,
                                'trace_record' : current_function_trace_link ,
                                'trace_argument_point' : next_function_trace_point_list ,
                                'reference_point' : reference_point
                            })
                    elif 'variant' == valid_trace_strategy_index['struct'] :
                        if last_trace_record_name == valid_trace_strategy_index['variant'] :
                            trace_link.append({
                                'file_name' : file_ast['file_name'] ,
                                'function' : function_name ,
                                'sub_function_trace' : [] ,
                                'trace_record' : current_function_trace_link ,
                                'trace_argument_point' : next_function_trace_point_list ,
                                'reference_point' : reference_point
                            })

                if last_trace_record_name in function_argument :
                    next_function_trace_point_list.append(function_argument.index(last_trace_record_name))

                    last_trace_record['line'] = function_declare_line  #  this is function argument and rewrite its line number ..

            if not len(next_function_trace_point_list) :
                continue

            sub_function_trace = []

            for reference_function_index in reference_function :  #  reference this function xref ..
                sub_function_trace_record = source_trace_data_stream_link(file_ast,{
                    'struct' : 'function' ,
                    'function' : function_name ,
                    'trace_point' : next_function_trace_point_list
                },valid_trace_strategy,reference_function_index)

                if not len(sub_function_trace_record):
                    continue

                sub_function_trace.append(sub_function_trace_record)

            trace_link.append({
                'file_name' : file_ast['file_name'] ,
                'function' : function_name ,
                'function_call' : sub_function_index['function_call'] ,
                'sub_function_trace' : sub_function_trace ,
                'trace_record' : current_function_trace_link ,
                'trace_argument_point' : next_function_trace_point_list ,
                'reference_point' : reference_point
            })

    return trace_link
    
def data_stream_trace(file_ast,source_strategy,valid_trace_strategy,source_trace_record) :  #  analayis xref data stream follow ..
    data_stream_trace_list = {}
    current_file_link = {
        'syntax' : [] ,
        'function' : []
    }
    
    #  we need to build trace link tree search by source_trace() .these trace link 
    #  are come from the same that file . 
    
    for source_trace_syntax_index in source_trace_record['syntax_trace'] :  #  search syntax xref ..
        current_file_name = source_trace_syntax_index['file_path']
        current_file_ast = pick_file_ast(file_ast,current_file_name)
        trace_link = source_trace_data_stream_link(current_file_ast,source_strategy,valid_trace_strategy,source_trace_syntax_index['sub_function'])
        
        if len(trace_link) :
            current_file_link['syntax'] += trace_link
    
    for source_trace_function_index in source_trace_record['function_trace'] :  #  search function xref ..
        current_file_name = source_trace_function_index['file_path']
        current_file_ast = pick_file_ast(file_ast,current_file_name)
        trace_link = source_trace_data_stream_link(current_file_ast,source_strategy,valid_trace_strategy,source_trace_function_index['sub_function'])
        
        if len(trace_link) :
            current_file_link['function'] += trace_link
    
    #  TIPS : filter invalid trace link by valid strategy again ..
    
    return current_file_link
    
    