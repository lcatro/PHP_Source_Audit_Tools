
#  coding : utf-8

import sys

import code_serialize
import data_stream_trace
import source_trace


class indent :
    
    __step_number = 2
    __space_number = 0
    
    @staticmethod
    def set_indent(indent_space_number) :
        indent.__space_number = indent_space_number

    @staticmethod
    def set_step_indent(step_space_number) :
        indent.__step_number = indent_space_number

    @staticmethod
    def enter_indent() :
        indent.__space_number += indent.__step_number

    @staticmethod
    def exit_indent() :
        indent.__space_number -= indent.__step_number

        if indent.__space_number < 0 :
            indent.__space_number = 0

    @staticmethod
    def make_string(length) :
        result = ''

        for index in range(length) :
            result += ' '

        return result

    @staticmethod
    def get_indent() :
        return indent.make_string(indent.__space_number)

    
def get_valid_sub_function_trace(sub_function_trace_record,trace_point,valid_trace_controlled_strategy_record) :
    result = []

    for sub_function_trace_record_index in sub_function_trace_record :
        function_name = sub_function_trace_record_index['function']
        reference_point = sub_function_trace_record_index['reference_point']
        trace_record = sub_function_trace_record_index['trace_record']
        trace_argument_point = sub_function_trace_record_index['trace_argument_point']
        sub_function = sub_function_trace_record_index['sub_function_trace']

        for trace_record_index in trace_record :
            last_record = trace_record_index[-1]
            trace_record_index_name = last_record['name']
            check_variant = ''
            array_index = ''

            if tuple == type(trace_record_index_name) :
                check_variant = trace_record_index_name[0]
                array_index = trace_record_index_name[1]
            else :
                check_variant = trace_record_index_name

            is_function_call = code_serialize.is_php_function(check_variant)
            is_variant = code_serialize.is_php_variant(check_variant)

            if not is_function_call and not is_variant :
                continue

            for trace_controlled_record_index in valid_trace_controlled_strategy_record :
                if is_function_call and 'function' == trace_controlled_record_index['struct'] :
                    funtion_name = trace_controlled_record_index['function']

                    if funtion_name == check_variant :  #  bingo ..
                        result.append({  #  WARNING !  adjust data output at it ..
                            'line' : trace_record_index['line'] ,
                            'function_argument' : trace_record_index['name'] ,
                            'function' : function_name
                        })

                elif is_variant and 'variant' == trace_controlled_record_index['struct'] :
                    variant_name = trace_controlled_record_index['variant']

                    if variant_name == check_variant :  #  bingo ..
                        result.append({
                            'line' : last_record['line'] ,
                            'function_argument' : last_record['name'] ,
                            'function' : function_name
                        })

        result += get_valid_reference_point(reference_point,trace_point,valid_trace_controlled_strategy_record)
        result += get_valid_sub_function_trace(sub_function,trace_argument_point,valid_trace_controlled_strategy_record)
        '''
        function_trace_point_list.append({
            'function' : function_name ,
            'trace_point' : trace_argument_point
        })
        '''

    return result

def get_valid_reference_point(reference_point,trace_point,valid_trace_controlled_strategy_record) :
    result = []

    for reference_point_index in reference_point :
        function_argument_list = reference_point_index['function_argument']

        for trace_point_index in trace_point :
            check_argument = function_argument_list[trace_point_index]
            check_variant = ''
            check_array_index = ''

            if tuple == type(check_argument) :  #  is array ..
                check_variant = check_argument[0]
                check_array_index = check_argument[1]
            else :
                check_variant = check_argument  #  is variant or value

            is_function_call = code_serialize.is_php_function(check_variant)
            is_variant = code_serialize.is_php_variant(check_variant)

            if not is_function_call and not is_variant :
                continue

            for trace_controlled_record_index in valid_trace_controlled_strategy_record :
                if is_function_call and 'function' == trace_controlled_record_index['struct'] :
                    funtion_name = trace_controlled_record_index['function']

                    if funtion_name == check_variant :  #  bingo ..
                        result.append(reference_point_index)

                elif is_variant and 'variant' == trace_controlled_record_index['struct'] :
                    variant_name = trace_controlled_record_index['variant']

                    if variant_name == check_variant :  #  bingo ..
                        result.append(reference_point_index)

    return result

def get_valid_sub_function_trace_by_deep_trace(sub_function_trace_record,valid_trace_controlled_strategy_record) :
    current_file_name = sub_function_trace_record['file_path']
    function_trace = sub_function_trace_record['function_trace']
    sub_function_trace = sub_function_trace_record['sub_function_trace']
    reference_point = {}
    link = []
    
    indent.enter_indent()
    
    for function_trace_index in function_trace :  #  this is analysis where will call at sub_function ..
        function_trace_reference_point = get_valid_function_trace(function_trace_index)
        
        if '__global' in function_trace_reference_point.keys() :
            global_reference = function_trace_reference_point['__global']
            file_path = global_reference['file_path']
            
            print indent.get_indent() + 'global reference :'
            
            for global_reference_index in global_reference ['global_call_point'] :
                print indent.get_indent() + file_path + ' (line:' + str(global_reference_index[-1]['line']) + ') function call : ' + \
                        global_reference_index[-1]['function_name'] , global_reference_index[-1]['function_argument']
            
            print ' '
            
        for function in function_trace_reference_point.keys() :
            if not reference_point.has_key(function) :
                reference_point[function] = function_trace_reference_point[function]
            else :
                reference_point[function]['function_call_point'] += function_trace_reference_point[function]['function_call_point']
                reference_point[function]['global_call_point'] += function_trace_reference_point[function]['global_call_point']
                
    for function_index in reference_point.keys() :
        link.append(reference_point[function_index])

    for sub_function_trace_index in sub_function_trace :  #  this is analysis where will reference it ..
        function_name = sub_function_trace_index['function']
        
        if function_name in reference_point.keys() :
            print indent.get_indent() + function_name + ' reference :'
            
            function_reference_record = reference_point[function_name]
            file_path = function_reference_record['file_path']
            
            indent.enter_indent()
            
            for function_call_point_index in function_reference_record['function_call_point'] :
                print indent.get_indent() + file_path + ' (line:' + str(function_call_point_index[-1]['line']) + ') function call : ' + \
                        function_call_point_index[-1]['function_name'] , function_call_point_index[-1]['function_argument']
            
            indent.exit_indent()
            
            print ' '
            
        sub_function_trace_link = get_valid_sub_function_trace_by_deep_trace(sub_function_trace_index,valid_trace_controlled_strategy_record)
        
    indent.exit_indent()

    return link

def get_valid_function_trace(function_trace) :
    file_path = function_trace['file_path']
    sub_function = function_trace['sub_function']
    reference_point = function_trace['reference_point']
    call_point = {}

    for sub_function_index in sub_function :
        function_name = sub_function_index['function']

        if not call_point.has_key(function_name) :
            call_point[function_name] = {
                'file_path' : file_path ,
                'function' : sub_function_index['function'] ,
                'function_call_point' : [] ,
                'global_call_point' : []
            }

        call_point[function_name]['function_call_point'].append(sub_function_index['function_call'])

    for reference_point_index in reference_point :
        function_name = reference_point_index['function_name']

        if not call_point.has_key(function_name) :
            call_point[function_name] = {
                'file_path' : file_path ,
                'function' : sub_function_index['function'] ,
                'function_call_point' : [] ,
                'global_call_point' : []
            }

        call_point[function_name]['global_call_point'].append(reference_point_index['reference_point'])

    return call_point

def search_link(deep_source_trace,find_function_name,valid_trace_controlled_strategy_record) :
    for deep_source_trace_function_index in deep_source_trace :
        sub_function_list = deep_source_trace_function_index['sub_function']
        
        for sub_function_index in sub_function_list :
            sub_function_name = sub_function_index['function']
            
            if not sub_function_name == find_function_name :  #  find link ..
                continue

            get_valid_sub_function_trace_by_deep_trace(deep_source_trace_function_index,valid_trace_controlled_strategy_record)
        
            
def deep_analysis_source_record(source_trace_record_data_stream_trace,deep_source_trace_record,valid_trace_controlled_strategy_record) :
    source_trace_function = source_trace_record_data_stream_trace['function']
    source_trace_syntax = source_trace_record_data_stream_trace['syntax']
    deep_source_trace_function = deep_source_trace_record['function']
    deep_source_trace_syntax = deep_source_trace_record['syntax']
    function_trace_point_list = []
    function_link = []
    syntax_link = []
    
    for source_trace_function_index in source_trace_function :
        file_name = source_trace_function_index['file_name']
        function_name = source_trace_function_index['function']
        function_call = source_trace_function_index['function_call']
        trace_point = source_trace_function_index['trace_argument_point']
        trace_record = source_trace_function_index['trace_record']
        reference_point = source_trace_function_index['reference_point']
        sub_function_trace = source_trace_function_index['sub_function_trace']
        current_function_trace = {
            'function' : function_name ,
            'file_name' : file_name ,
            'trace_point' : trace_point ,
            'trace_link' : [] ,
            'global_trace' : [] ,
            'trace_record' : trace_record
        }
        trace_link = current_function_trace['trace_link']
        global_trace = current_function_trace['global_trace']
        
        current_function_valid_reference_point = get_valid_reference_point(reference_point,trace_point,valid_trace_controlled_strategy_record)
        sub_function_valid_sub_function_trace = get_valid_sub_function_trace(sub_function_trace,trace_point,valid_trace_controlled_strategy_record)
        
        if len(current_function_valid_reference_point) :
            global_trace += current_function_valid_reference_point
            
        if len(sub_function_valid_sub_function_trace) :
            trace_link += sub_function_valid_sub_function_trace
        
        if len(trace_link) or len(global_trace) :
            print function_name + '(' , trace_point , ') : '
            
            indent.enter_indent()
            
            for function_call_index in function_call :
                print indent.get_indent() + file_name + ' (line:' + str(function_call_index['line']) + ') syntax:' + function_call_index['function_name'] , function_call_index['function_argument']
            
            indent.exit_indent()
            
            #search_link(deep_source_trace_function,function_name,valid_trace_controlled_strategy_record)
            
            function_link.append(current_function_trace)
            function_trace_point_list.append({
                'function' :  function_name ,
                'trace_point' : trace_point 
            })
    
    for source_trace_syntax_index in source_trace_syntax :
        file_name = source_trace_syntax_index['file_name']
        function_name = source_trace_syntax_index['function']
        function_call = source_trace_syntax_index['function_call']
        trace_point = source_trace_syntax_index['trace_argument_point']
        trace_record = source_trace_syntax_index['trace_record']
        reference_point = source_trace_syntax_index['reference_point']
        sub_function_trace = source_trace_syntax_index['sub_function_trace']
        current_function_trace = {
            'function' : function_name ,
            'file_name' : file_name ,
            'trace_point' : trace_point ,
            'trace_link' : [] ,
            'global_trace' : [] ,
            'trace_record' : trace_record
        }
        trace_link = current_function_trace['trace_link']
        global_trace = current_function_trace['global_trace']
        
        for reference_point_index in reference_point :
            reference_point_ = reference_point_index['reference_point']
            current_function_valid_reference_point = get_valid_reference_point(reference_point_,trace_point,valid_trace_controlled_strategy_record)
            
            if len(current_function_valid_reference_point) :
                global_trace += current_function_valid_reference_point
            
        for sub_function_trace_index in sub_function_trace :
            sub_function_valid_sub_function_trace = get_valid_sub_function_trace(sub_function_trace_index,trace_point,valid_trace_controlled_strategy_record)
            
            if len(sub_function_valid_sub_function_trace) :
                trace_link += sub_function_valid_sub_function_trace
                
        if len(trace_link) or len(global_trace) :
            print function_name + '(' , trace_point , ') : '
            
            indent.enter_indent()
            
            for function_call_index in function_call :
                print indent.get_indent() + file_name + ' (line:' + str(function_call_index['line']) + ') syntax:' + function_call_index['syntax'] , function_call_index['syntax_argument']
            
            indent.exit_indent()
            
            #search_link(deep_source_trace_syntax,function_name,valid_trace_controlled_strategy_record)
            
            syntax_link.append(current_function_trace)
            function_trace_point_list.append({
                'function' :  function_name ,
                'trace_point' : trace_point 
            })

    
    return function_link + syntax_link

def scan_source(file_path,trace_strategy_record,valid_trace_controlled_strategy_record) :
    file_ast = source_trace.load_file_ast(sys.argv[1])
    
    source_trace_record = source_trace.source_trace(file_ast,trace_strategy_record)
    
    source_trace.json_debug_print(source_trace_record)
    
    source_trace_record_data_stream_trace = data_stream_trace.data_stream_trace(file_ast,trace_strategy_record,valid_trace_controlled_strategy_record,source_trace_record)
    deep_source_trace_record = source_trace.deep_source_trace(file_ast,source_trace_record,source_trace_record_data_stream_trace,valid_trace_controlled_strategy_record)
    
    return source_trace_record_data_stream_trace , deep_source_trace_record


if __name__ == '__main__' :
    if 2 == len(sys.argv) :
        trace_strategy_record = source_trace.source_trace_strategy_load('./call_strategy.txt')
        valid_trace_controlled_strategy_record = source_trace.source_trace_strategy_load('./valid_trace_strategy.txt')
        source_trace_record_data_stream_trace , deep_source_trace_record = scan_source(sys.argv[1],trace_strategy_record,valid_trace_controlled_strategy_record)
        
        print 'source_trace_record_data_stream_trace output :'
        
        source_trace.json_debug_print(source_trace_record_data_stream_trace)
        
        print 'deep_source_trace_record output :'
        
        source_trace.json_debug_print(deep_source_trace_record)
        
        analysis_source_record = deep_analysis_source_record(source_trace_record_data_stream_trace,deep_source_trace_record,valid_trace_controlled_strategy_record)
        
        print 'deep_analysis_source_record output :'
        
        source_trace.json_debug_print(analysis_source_record)
        
    else :
        print 'cade_analysis.py %path'
        
