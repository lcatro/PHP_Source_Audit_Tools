
# coding: utf-8

import copy
import json
import os
import pickle
import sys

import code_serialize
import data_stream_trace
import file_system


def resolve_function_trace_strategy_line(line_data) :
    left_parentheses = line_data.find('(')
    right_parentheses = line_data.find(')')
    
    if not -1 == left_parentheses and not -1 == right_parentheses and left_parentheses < right_parentheses :
        trace_point = []
        argument_list = line_data.split(',')
        
        for argument_index in range(len(argument_list)) :
            argument_index_data = argument_list[argument_index].strip()
            
            if not -1 == argument_index_data.find('{') and not -1 == argument_index_data.find('}') :
                trace_point.append(argument_index)
               
        return {
            'struct' : 'function' ,
            'function' : line_data[ : left_parentheses].strip() ,
            'trace_point' : trace_point
        }
    else :
        print 'Syntax Error in' , line_data
    
    return False

def resolve_syntax_trace_strategy_line(line_data) :
    split_flag = line_data.find('#')
    
    if not -1 == split_flag :
        trace_point = []
        argument_list = line_data.split(',')
        
        for argument_index in range(len(argument_list)) :
            argument_index_data = argument_list[argument_index].strip()
            
            if not -1 == argument_index_data.find('{') and not -1 == argument_index_data.find('}') :
                trace_point.append(argument_index)
               
        if len(trace_point) :
            return {
                'struct' : 'syntax' ,
                'syntax' : line_data[ : split_flag].strip() ,
                'trace_point' : trace_point
            }
    else :
        print 'Syntax Error in' , line_data
        
    return False

def resolve_variant_trace_strategy_line(line_data) :
    array_flag_left = line_data.find('[')
    array_flag_right = line_data.find(']')

    if not -1 == array_flag_left and not -1 == array_flag_right :
        array_list = line_data[array_flag_left +1 : array_flag_right].split(',')
        
        for array_index in array_list :
            array_index = array_index.strip()
        
        return {
            'struct' : 'variant' ,
            'variant' : array_name ,
            'trace_point' : array_list
        }
    elif not -1 == array_flag_left or not -1 == array_flag_right :
        print 'Syntax Error in' , line_data
        
        return False
    
    return {
            'struct' : 'variant' ,
            'variant' : line_data ,
            'trace_point' : []
    }

def source_trace_strategy_load(strategy_file_path) :
    '''
        # strategy note             <= strategy note
        
        function(arg1,{arg2},arg3)  <= trace function ,focus on arg2
        
        example :
          phpinfo()
          system({arg1})
          test(arg1,{arg2},arg3)
        
        keyword {}                  <= trace syntax ,foucus on keyword argument 1
        
        example :
          include#{arg1}
          eval#{arg1}
    '''
    
    strategy_file = open(strategy_file_path)
    
    if strategy_file :
        trace_strategy = []
        
        '''
            format trace strategy :
            [
                {
                    'struct' : 'syntax' ,
                    'syntax' : 'name' ,
                    'trace_point' : syntax_expression
                } ,
                {
                    'struct' : 'function' ,
                    'function' : 'name' ,
                    'trace_point' : [argument_list]
                } ,
                {
                    'struct' : 'variant' ,
                    'variant' : 'name' ,
                    'trace_point' : [array_index]  #  just support when it is an array variant ..
                }
            ]
        '''
        
        for file_line in strategy_file :
            file_line = file_line.strip()
            
            if not len(file_line) or file_line.startswith('#') :
                continue
                
            if not -1 == file_line.find('#') :
                tarce_record = resolve_syntax_trace_strategy_line(file_line)
            elif file_line.startswith('$') :
                tarce_record = resolve_variant_trace_strategy_line(file_line)
            else :
                tarce_record = resolve_function_trace_strategy_line(file_line)
            
            if tarce_record :
                trace_strategy.append(tarce_record)
            
        return trace_strategy
    
    return False

def get_source_trace_strategy_by_function(source_strategy,function_name) :
    if dict == type(source_strategy) :
        source_strategy = [source_strategy]

    for source_strategy_index in source_strategy :
        if 'function' == source_strategy_index['struct'] :
            if function_name == source_strategy_index['function'] :
                return source_strategy_index

    return False

def get_source_trace_strategy_by_syntax(source_strategy,syntax_keyword) :
    if dict == type(source_strategy) :
        source_strategy = [source_strategy]

    for source_strategy_index in source_strategy :
        if 'syntax' == source_strategy_index['struct'] :
            if syntax_keyword == source_strategy_index['syntax'] :
                return source_strategy_index

    return False

def function_trace(file_ast_quick_index,source_strategy,current_function_name = '__global') :  #  TIPS :  source_strategy is a list object ..
    if not file_ast_quick_index :
        return False

    if not len(file_ast_quick_index) and not len(source_strategy) :
        return False
        
    def find_trace_call(file_ast_quick_index,function_name) :  #  search function call by function name in quick ast index ..
        function_call_list = file_ast_quick_index['function_call']
        bingo_function_call = {
            'current_function' : [] ,
            'sub_function' : []
        }
        
        for function_call_index in function_call_list :
            if function_name == function_call_index['function_name'] :
                bingo_function_call['current_function'].append(function_call_index)
        
        subfunction_list = file_ast_quick_index['subfunction_list']
        
        for subfunction_index in subfunction_list :
            subfunction_index_bingo_function_call = find_trace_call(subfunction_index,function_name)  #  search function call in function ast ..
            
            if len(subfunction_index_bingo_function_call['current_function']) or len(subfunction_index_bingo_function_call['sub_function']) :
                bingo_function_call['sub_function'].append({
                    'function' : subfunction_index['function'] ,
                    'function_call' : subfunction_index_bingo_function_call['current_function'] ,
                    'subfunction_call' : subfunction_index_bingo_function_call['sub_function']
                })
        
        return bingo_function_call
    
    def xref_trace(file_ast_quick_index,find_result) :  #  search function xref ..
        sub_function = []
        reference_point = []

        for find_result_index in find_result['sub_function'] :
            reference_function_list = None

            if code_serialize.is_php_class(find_result_index['function']) :  #  class ..
                class_function_list = []

                for class_function_index in find_result_index['subfunction_call'] :
                    find_sub_function_result = find_trace_call(file_ast_quick_index,class_function_index['function']) 
                    reference_function_list = xref_trace(file_ast_quick_index,find_sub_function_result)
                    
                    for reference_point_index in reference_function_list['reference_point'] :
                        for reference_sub_function_index in reference_function_list['sub_function'] :
                            if reference_sub_function_index['function'] == reference_point_index['function_name'] and \
                               not reference_point_index['reference_point'] in reference_sub_function_index['reference_point'] :
                                reference_sub_function_index['reference_point'] += reference_point_index['reference_point']

                    class_function_list.append({
                        'function' : class_function_index['function'] ,  #  class name
                        'function_call' : class_function_index['function_call'] ,
                        'subfunction_call' : class_function_index['subfunction_call'] ,
                        'reference_function' : reference_function_list['sub_function'] ,
                        'reference_point' : find_sub_function_result['current_function']
                    })

                sub_function.append({
                    'function' : find_result_index['function'] ,  #  class name
                    'function_call' : find_result_index['function_call'] ,
                    'subfunction_call' : class_function_list ,
                    'reference_function' : [] ,
                    'reference_point' : []
                })
            else :
                find_sub_function_result = find_trace_call(file_ast_quick_index,find_result_index['function'])  #  search where will call these functions ..
                reference_function_list = xref_trace(file_ast_quick_index,find_sub_function_result)  #  recursion find all reference these functions ..

                for reference_point_index in reference_function_list['reference_point'] :
                    for reference_sub_function_index in reference_function_list['sub_function'] :
                        if reference_sub_function_index['function'] == reference_point_index['function_name'] and \
                           not reference_point_index['reference_point'] in reference_sub_function_index['reference_point'] :
                            reference_sub_function_index['reference_point'] += reference_point_index['reference_point']

                sub_function.append({
                    'function' : find_result_index['function'] ,
                    'function_call' : find_result_index['function_call'] ,
                    'subfunction_call' : find_result_index['subfunction_call'] ,
                    'reference_function' : reference_function_list['sub_function'] ,
                    'reference_point' : []
                })
                reference_point.append({
                    'function_name' : find_result_index['function'] ,
                    'subfunction_call' : find_result_index['subfunction_call'] ,
                    'function_call' : find_result_index['function_call'] ,
                    'reference_point' : find_sub_function_result['current_function']
                })
            
        return {
            'sub_function' : sub_function ,
            'reference_point' : reference_point
        }
    
    sub_function = []
    reference_point = []
    
    for source_strategy_index in source_strategy :
        if 'function' == source_strategy_index['struct'] :
            find_result = find_trace_call(file_ast_quick_index,source_strategy_index['function'])  #  search these functions which call eval function ..
            reference_function_list = xref_trace(file_ast_quick_index,find_result)  #  recursion find all reference these functions ..
            
            for sub_function_index in reference_function_list['sub_function'] :
                sub_function.append(sub_function_index)
                    
            for reference_function_index in reference_function_list['reference_point'] :
                for sub_function_index in sub_function :
                    if sub_function_index['function'] == reference_function_index['function_name'] :
                        sub_function_index['reference_point'] += reference_function_index['reference_point']
                        
                        break
                            
            if len(find_result['current_function']) :
                current_function_reference_point = [] + find_result['current_function']
                    
                reference_point.append({
                    'function_name' : current_function_name ,
                    'subfunction_call' : [] ,
                    'function_call' : [] ,
                    'reference_point' : current_function_reference_point
                })
        
    return {
        'sub_function' : sub_function ,
        'reference_point' : reference_point ,
    }
    
def syntax_trace(file_ast,source_strategy) :
    if not len(file_ast) and not len(source_strategy) :
        return False
    
    def find_syntax_call(file_ast,syntax_name,current_function = '__global') :
        bingo_syntax = {
            'function' : current_function ,
            'function_call' : [] ,           #  it mean syntax information ..
            'reference_function' : [] ,
            'reference_point' : []
        }
        
        for ast_index in file_ast :
            ast_struct_type = code_serialize.get_php_ast_struct_type(ast_index)
            
            if syntax_name == ast_struct_type :
                syntax_argument_list = code_serialize.get_syntax_argument_list(ast_index)
                
                bingo_syntax['function_call'].append({
                    'syntax' : syntax_name ,
                    'syntax_argument' : syntax_argument_list ,
                    'line' : ast_index.lineno
                })
            elif 'function' == ast_struct_type :
                subfunction_bingo_syntax = find_syntax_call(ast_index.nodes,syntax_name,ast_index.name)
                
                if len(subfunction_bingo_syntax['reference_function']) or len(subfunction_bingo_syntax['function_call']) :
                    bingo_syntax['reference_function'].append(subfunction_bingo_syntax)
                
        return bingo_syntax
    
    def xref_trace(file_ast,find_result) :
        xref_list = []
        
        for find_result_index in find_result['reference_function'] :
            file_ast_quick_index = code_serialize.build_ast_index(file_ast)
            reference_function_list = function_trace(file_ast_quick_index,[{  #  search function xref ..
                'struct' : 'function' ,
                'function' : find_result_index['function'] ,
                'trace_point' : []  #  WARNING ! syntax_trace is search for xref but not trace data stream ..
            }])

            xref_list.append({
                'function' : find_result_index['function'] ,
                'function_call' : find_result_index['function_call'] ,
                'reference_function' : find_result_index['reference_function'] , 
                'sub_function' : reference_function_list['sub_function'] ,
                'reference_point' : reference_function_list['reference_point']
            })
            
        return xref_list
    
    sub_function = []
    reference_point = []
    
    for source_strategy_index in source_strategy :
        if 'syntax' == source_strategy_index['struct'] :
            find_result = find_syntax_call(file_ast,source_strategy_index['syntax'])
            reference_function_list = xref_trace(file_ast,find_result)
            
            for sub_function_index in find_result['reference_function'] :  #  add direct reference syntax ..
                if len(sub_function_index) :
                    sub_function.append(sub_function_index)
            
            if len(find_result['function_call']) :  #  current function reference ..
                for reference_function_index in find_result['function_call'] :
                    reference_point.append({
                        'reference_point' : reference_function_index ,
                        'function_name' : '__global'
                    })
                    
            for reference_function_index in reference_function_list :  #  add indirect(function inside) reference syntax trace ..
                for sub_function_index in sub_function :
                    if not reference_function_index['function'] == sub_function_index['function'] :  #  search function in reference_function_list ..
                        continue

                    for reference_point_index in reference_function_index['reference_point'] :
                        sub_function_index['reference_point'].append(reference_point_index)

                    for sub_function_index_ in reference_function_index['sub_function'] :
                        sub_function_index['reference_function'].append(sub_function_index_)
                            
    return {
        'sub_function' : sub_function ,
        'reference_point' : reference_point
    }
    
def load_file_ast(file_path) :  #  load ast with files ..
    file_list = []
    file_ast_list = []
    file_ast_quick_index_list = []
    
    if os.path.isfile(file_path) :
        file_list.append(file_path)
    elif os.path.isdir(file_path) :
        for dir_index in os.walk(file_path) :
            dir_path = dir_index[0] + file_system.get_system_directory_separator()
            
            for dir_file_index in dir_index[2] :
                if 'php' == file_system.get_extension_name(dir_file_index) :
                    file_list.append(dir_path + dir_file_index)
    else :
        return False
    
    if not len(file_list) :
        return False
                
    for file_index in file_list :  #  using strategy for search xref of eval function ..
        if os.path.exists(file_index + '.ast') and os.path.exists(file_index + '.ast_index') :
            file_ast = file_system.read_file(file_index + '.ast')
            file_ast_quick_index = file_system.read_file(file_index + '.ast_index')
            file_ast = pickle.loads(file_ast)
            file_ast_quick_index = pickle.loads(file_ast_quick_index)
        else :
            file_ast = code_serialize.convert_ast(file_index)
            file_ast_quick_index = code_serialize.build_ast_index(file_ast)
            
        file_ast_list.append({
            'file_path' : file_system.get_relative_path(file_index,file_path) ,
            'file_ast' : file_ast
        })
        file_ast_quick_index_list.append({
            'file_path' : file_system.get_relative_path(file_index,file_path) ,
            'file_ast' : file_ast_quick_index
        })
        
    return {
        'file_ast_list' : file_ast_list ,
        'file_ast_quick_index_list' : file_ast_quick_index_list
    }
    
def source_trace(file_ast,source_strategy) :  #  scan source for analayis xref by strategy ..
    if not len(source_strategy) :
        return False
    
    function_trace_list = []
    syntax_trace_list = []
    
    for file_quick_ast_index in file_ast['file_ast_quick_index_list'] :  #  first scan code by user's source strategy ..
        function_trace_result = function_trace(file_quick_ast_index['file_ast'],source_strategy)
        
        if not function_trace_result :
            continue
        
        function_trace_result['file_path'] = file_quick_ast_index['file_path']
        
        function_trace_list.append(function_trace_result)
        
    for file_ast_index in file_ast['file_ast_list'] :
        syntax_trace_index = syntax_trace(file_ast_index['file_ast'],source_strategy)
        
        if not syntax_trace_index :
            continue
        
        syntax_trace_index['file_path'] = file_ast_index['file_path']
        
        syntax_trace_list.append(syntax_trace_index)

    return {
        'function_trace' : function_trace_list ,
        'syntax_trace' : syntax_trace_list
    }

def deep_source_trace(file_ast,source_trace_result,source_data_stream_trace,valid_trace_strategy) :  #  using source_trace() quick analayis results to search these call link in all files ..
    function_trace_list = source_trace_result['function_trace']  #  all files functions trace result ..
    syntax_trace_list = source_trace_result['syntax_trace']  #  all files syntax trace result ..
        
    def get_all_sub_function(file_ast,function_trace) :  #  recursing function trace result for dig full function name ..
        return_function_name_list = []
        
        if dict == type(function_trace) :  #  is function trace object ..
            current_function_name = function_trace['function']
            
            return_function_name_list.append(current_function_name)
            
            return return_function_name_list
        elif list == type(function_trace) :  #  is function trace list ..
            for function_trace_index in function_trace :
                current_function_name = function_trace_index['function']

                if not code_serialize.is_php_class(current_function_name) and not current_function_name in return_function_name_list :
                    return_function_name_list.append(current_function_name)
                
                for reference_function_index in function_trace_index['reference_function'] :
                    return_function_name_list += get_all_sub_function(file_ast,reference_function_index)
                    
        return return_function_name_list
        
    def remove_file_ast(file_ast,file_path) :
        file_ast_backup = copy.deepcopy(file_ast)
        file_ast_quick_index_list = file_ast_backup['file_ast_quick_index_list']
        file_ast_list = file_ast_backup['file_ast_list']
        
        for file_ast_quick_index in file_ast_quick_index_list :
            if file_ast_quick_index['file_path'] == file_path :
                file_ast_quick_index_list.remove(file_ast_quick_index)
                
                break
            
        for file_ast_index in file_ast_list :
            if file_ast_index['file_path'] == file_path :
                file_ast_list.remove(file_ast_index)
                
                break
            
        return file_ast_backup
        
    def build_data_stream_trace_by_record(file_ast,current_file_name,function_trace,source_data_stream_trace,valid_trace_strategy) :
        return_record = []
        current_file_ast = data_stream_trace.pick_file_ast(file_ast,current_file_name)
        
        if dict == type(function_trace) :  #  is function trace object ..
            current_function_name = function_trace['function']
            trace_point_list = []

            for source_data_stream_trace_index in source_data_stream_trace :
                if current_function_name == source_data_stream_trace_index['function'] :
                    trace_point_list = source_data_stream_trace_index['trace_argument_point']

                    break

            if len(trace_point_list) :
                for function_call_index in function_trace['function_call'] :
                    return_record.append({
                        'function_name' : current_function_name ,
                        'trace_record' : data_stream_trace.function_inside_data_stream_trace(current_file_ast,valid_trace_strategy,current_function_name,function_call_index,trace_point_list)
                    })
        elif list == type(function_trace) :  #  is function trace list ..
            for function_trace_index in function_trace :
                current_function_name = function_trace_index['function']

                if not code_serialize.is_php_class(current_function_name) :
                    trace_point_list = []
                    
                    for source_data_stream_trace_index in source_data_stream_trace :
                        if current_function_name == source_data_stream_trace_index['function'] :
                            trace_point_list = source_data_stream_trace_index['trace_argument_point']
                            
                            break
                            
                    if not len(trace_point_list) :
                        continue
                    
                    for function_call_index in function_trace_index['function_call'] :
                        return_record.append({
                            'function_name' : current_function_name ,
                            'trace_record' : data_stream_trace.function_inside_data_stream_trace(current_file_ast['file_ast'],valid_trace_strategy,current_function_name,function_call_index,trace_point_list)
                        })
                    
                for reference_function_index in function_trace_index['reference_function'] :  #  is class ..
                    return_record += build_data_stream_trace_by_record(file_ast,current_file_name,reference_function_index,source_data_stream_trace,valid_trace_strategy)
                    
        return return_record
        
    def apply_data_stream_search_result_into_function_trace(other_function_trace,other_function_data_stream_trace) :
        function_trace_record = other_function_trace['function_trace']
        function_data_stream_trace_record = other_function_data_stream_trace['function']
        
        for function_trace_record_index in function_trace_record :
            function_sub_function = function_trace_record_index['sub_function']
            
            for function_sub_function_index in function_sub_function :
                function_name = function_sub_function_index['function']
                
                if not function_trace_record_index.has_key('trace_record') :
                    function_trace_record_index['trace_record'] = []
                if not function_trace_record_index.has_key('trace_argument_point') :
                    function_trace_record_index['trace_argument_point'] = []
                    
                for function_data_stream_trace_record_index in function_data_stream_trace_record :
                    if function_name == function_data_stream_trace_record_index['function'] :
                        function_trace_record_index['trace_record'] += function_data_stream_trace_record_index['trace_record']
                        function_trace_record_index['trace_argument_point'] = function_data_stream_trace_record_index['trace_argument_point']
        
    def deep_function_trace(file_ast,function_trace_list,source_data_stream_trace,valid_trace_strategy,had_search_function = []) :
        function_trace_link = []
        
        for function_trace_index in function_trace_list :  #  trace function from search result ..
            current_function_trace_index_file_name = function_trace_index['file_path']
            sub_function_list = function_trace_index['sub_function']
            trance_function_list = get_all_sub_function(file_ast,sub_function_list)
            
            data_stream_trace_record = build_data_stream_trace_by_record(file_ast,current_function_trace_index_file_name,sub_function_list,source_data_stream_trace,valid_trace_strategy)
            
            if not len(trance_function_list) :
                continue
            
            for trance_function_index in trance_function_list :
                if trance_function_index in had_search_function :
                    continue
                    
                trace_strategy = {
                    'struct' : 'function' ,
                    'function' : trance_function_index ,
                    'trace_point' : get_trace_point_at_data_stream_record_by_function_name(source_data_stream_trace,trance_function_index)
                }

                search_ast_list = remove_file_ast(file_ast,current_function_trace_index_file_name)
                other_function_trace = source_trace(search_ast_list,[trace_strategy])  #  source trace these function in other files ..
                other_function_data_stream_trace = data_stream_trace.data_stream_trace(file_ast,[trace_strategy],valid_trace_strategy,other_function_trace)

                apply_data_stream_search_result_into_function_trace(other_function_trace,other_function_data_stream_trace)

                recursing_function_trace = other_function_trace['function_trace']
                had_search_function.append(trance_function_index)  #  tag don't search these had trace function again ..
                #  recursing matching where call these function ..
                recursing_function_trace_link = deep_function_trace(file_ast,recursing_function_trace,source_data_stream_trace,valid_trace_strategy,had_search_function)

                function_trace_link.append({
                    'file_path' : current_function_trace_index_file_name ,
                    'function_trace' : recursing_function_trace ,
                    'sub_function_trace' : recursing_function_trace_link ,
                    'trace_record' : data_stream_trace_record ,
                    'function' : trance_function_index
                })
            
        return function_trace_link
        
    if 1 < len(function_trace_list) :  #  mutil files matching ,it need to recursion for search function call link ..
        return {
            'function' : deep_function_trace(file_ast,function_trace_list,source_data_stream_trace['function'],valid_trace_strategy) ,
            'syntax' : deep_function_trace(file_ast,syntax_trace_list,source_data_stream_trace['syntax'],valid_trace_strategy)
        }
    
    return {
        'function' : source_trace_result['function_trace'] ,
        'syntax' : source_trace_result['syntax_trace']
    }

def get_deep_source_trace_record(trace_record,record_type,file_name) :
    trace_record = trace_record[record_type]
    
    for trace_record_index in trace_record :
        if file_name == trace_record_index['file_path'] :
            return trace_record_index
    
    return False
    
def get_trace_point_at_data_stream_record_by_function_name(source_data_stream_trace,function_name) :
    for source_data_stream_trace_index in source_data_stream_trace :
        if function_name == source_data_stream_trace_index['function'] :
            return source_data_stream_trace_index['trace_argument_point']
        
    return []
    
def format_trace_link(source_trace_result) :
    function_trace = source_trace_result['function_trace']
    syntax_trace = source_trace_result['syntax_trace']
    
    def xref_function_output(sub_function_index,function_trace_link = []) :
        reference_function = sub_function_index['reference_function']

        if len(reference_function) :
            for reference_function_index in reference_function :
                xref_function_output(reference_function_index,function_trace_link + [reference_function_index['function']])
        else :
            output_string = ''
            
            for function_trace_index in function_trace_link :
                output_string += function_trace_index + ' -> '
            
            if len(output_string) :
                output_string = output_string[:-3]
            
            print output_string

    for function_trace_index in function_trace :
        for sub_function_index in function_trace_index['sub_function'] :
            if len(sub_function_index['function_call']) :
                xref_function_output(sub_function_index,[sub_function_index['function_call'][0]['function_name'] ,sub_function_index['function']])

        for reference_point_index in function_trace_index['reference_point'] :
            for reference_point_index_ in reference_point_index['reference_point'] :
                print 'global reference :' , reference_point_index_['function_name'] , reference_point_index_['function_argument']

def json_debug_print(json_data) :
    print json.dumps(json_data,indent=4)

if __name__ == '__main__' :
    if not 4 == len(sys.argv) :
        print 'arg'
        
        exit()
        
    file_ast = load_file_ast(sys.argv[1])
    trace_strategy_record = source_trace_strategy_load(sys.argv[2])
    valid_trace_controlled_strategy_record = source_trace_strategy_load(sys.argv[3])
    source_trace_record = source_trace(file_ast,trace_strategy_record)
    current_file_link = data_stream_trace.data_stream_trace(file_ast,trace_strategy_record,valid_trace_controlled_strategy_record,source_trace_record)
    deep_source_trace_record = deep_source_trace(file_ast,source_trace_record,current_file_link,valid_trace_controlled_strategy_record)
    
#    json_debug_print(source_trace_record)
#    format_trace_link(source_trace_record)
    json_debug_print(current_file_link)
    json_debug_print(deep_source_trace_record)

    
    