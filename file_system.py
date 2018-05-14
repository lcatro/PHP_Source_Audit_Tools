
import os
import platform
import sys


def debug_print(debug_string) :
    print debug_string
    
def debug_var_dump(debug_object) :
    print debug_object

def get_timetick() :
    return time.time()

def get_system() :
    system = platform.system()
    
    if 'Windows' == system :
        return 1
    if 'Linux' == system :
        return 2
    if 'MacOS' == system :
        return 3
    
    return 0
    
def get_system_directory_separator() :
    if 1 == get_system() :
        return '\\'
    
    return '/'
    
def get_current_path() :
    offset = sys.argv[0].rfind(get_system_directory_separator())
        
    current_file_path = sys.argv[0][ : offset + 1]
    
    return current_file_path

def get_file_name(file_path) :
    offset = file_path.rfind(get_system_directory_separator())
    
    if -1 == offset :
        return file_path
    
    return file_path[offset + 1 : ]

def get_relative_path(file_path,dir_path) :
    if file_path == dir_path :
        return get_file_name(file_path)
    elif file_path.startswith(dir_path) :
        if get_system_directory_separator() == dir_path[-1] :
            return file_path[len(dir_path) : ]
        else :
            return file_path[len(dir_path) + 1 : ]
        
    return get_file_name(file_path)

def get_extension_name(file_path) :
    offset = file_path.rfind('.')
    
    if not -1 == offset :
        return file_path[offset + 1 : ]
        
    return ''

def get_directory_files(directory_path) :
    return os.listdir(directory_path)
    
def is_exist_directory(path) :
    return os.path.isdir(path)
    
def is_exist_file(path) :
    return os.path.isfile(path)
    
def create_directory(path) :
    return os.mkdir(path)
    
def copy_file(source_file_path,destination_file_path) :
    source_file_data = read_file(source_file_path)
    
    write_file(destination_file_path,source_file_data)
    
def copy_directory(source_path,destination_path) :
    directory_char = get_system_directory_separator()
    
    if not is_exist_directory(destination_path) :
        os.mkdir(destination_path)
            
    for walk_index in os.walk(source_path) :
        walk_source_path = walk_index[0]
        
        first_directory_offset = walk_source_path.find(directory_char)

        if not -1 == first_directory_offset :
            copy_target_directory = destination_path + directory_char + walk_index[0][first_directory_offset + 1:]
        else :
            copy_target_directory = destination_path + directory_char
        
        if not is_exist_directory(copy_target_directory) :
            os.mkdir(copy_target_directory)
        
        for file_index in walk_index[2] :
            copy_file(walk_index[0] + directory_char + file_index,copy_target_directory + directory_char + file_index)

def read_file(file_path) :
    file = open(file_path,'r')
    result = ''
    
    if file :
        result = file.read()
        
    file.close()
    
    return result
    
def write_file(file_path,data) :
    file = open(file_path,'w')
    
    if file :
        file.write(data)
        
    file.close()
    
