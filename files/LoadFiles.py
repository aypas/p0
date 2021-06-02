import os
import re
import sys
import pickle
import paths

class TooManyDuplicates(Exception):
    def __init__(self, msg):
        self.msg = msg

class Payload:
    # this is a static variable which determines where all unpacked files be placed
    # changing this is only possible in the config.json file

    #need to change this as the pickled object will send to a server its own client dump_folder
    dump_folder = "received"

    def __init__(self, root_folder : str, pwd=".", flatten : bool = False, files_to_read=list()):
        '''
        root_folder is where the contents of the data will be unpacked within the dump_folder static variable
            sender must set this variable, but if receiver has a folder of the same name, they too can change it.
        current_working_directory is where the search for all files/folders will begin
        __files_to_read is an optional arg to limit the number of files to read to the given names (paths must be absolute)
        self.payload is the data that has been traversed by get_files_wrapper i.e the data file/folder data
        '''
        self.root_folder = root_folder
        self.current_working_directory = pwd
        self.payload = []
        self.flatten = flatten
        self.__files_to_read = files_to_read
        # the format of payload is a list of dictionaries where {full_path: str, data: []byte, is_folder: bool}

    @property
    def windows(self):
        # if platform is windows, property returns true, else false
        return "win" in sys.platform

    def __recursive_files_and_folders(self, dir : str = None, data : list = None) -> list:
        if dir is None:
            print("here")
            files_and_folders = os.scandir(self.current_working_directory)
            payload = list()
        else:
            files_and_folders = os.scandir(dir)
            payload = data

        for item in files_and_folders:
            print(item.name, "\t",item.path, "poop", paths.path(item.path, self.windows))
            if item.is_dir():
                path, name = paths.path(item.path, self.windows)
                folder = {"path": path, "name": name, "is_folder": True, "data": []}
                payload.append(folder)
                self.__recursive_files_and_folders(dir=self.current_working_directory+"/"+folder["path"]+"/"+folder["name"], data=folder["data"])
                continue
            
            # keep an eye on encoding, might cause errors in the future...should be communicated to server
            path, name = paths.path(item.path, self.windows)
            file_data = open(item.path, "r", encoding="mbcs")
            payload.append({"path": path, "name": name, "data": file_data.read(), "is_folder": False })
            file_data.close()
        return payload

    def __get_files_and_folders(self) -> list:
        files = list()
        for file_path in self.__files_to_read:
            try:
                path, name = paths.path(item.path, self.windows)
                file = open(file_path, "r")
                files.append({"path": path, "name": name, "data": file.read(), "is_folder": False})
                file.close()
            except FileNotFoundError as e:
                print(e)
        return files

    def get_files(self) -> None:
        if len(self.__files_to_read) == 0:
            self.payload = self.__recursive_files_and_folders()
        else:
            self.payload = self.__get_files_and_folders()

    def create_unpacking_dir(self):
        try:
            os.mkdir(self.dump_folder+"/"+self.root_folder)
            return None
        except FileExistsError:
            for i in range(1,20):
                print("how?")
                try:
                    os.mkdir(self.dump_folder+"/"+self.root_folder+"-"+str(i))
                    self.root_folder = self.root_folder+"-"+str(i)
                    return None
                except Exception as e:
                    pass
        raise TooManyDuplicates("Clean up your received folder or change instance variable root_folder. You have too many duplicates.")

    def unpack_files(self, payload, flatten = False) -> bool:
        if len(payload) == 0:
            return False

        dump_in = f"{self.dump_folder}/{self.root_folder}/"

        for item in payload:
            if item["is_folder"]:
                if not flatten:
                    os.mkdir(dump_in + f"{item['path']}/{item['name']}")
                success = self.unpack_files(item["data"], flatten)
                if not success:
                    return False
                continue
            
            try:
                path = item["name"] if flatten == True else f"{item['path']}/{item['name']}/"
                file = open(dump_in+"/"+path , "w")
                file.write(item["data"])
                file.close()
            except Exception as e:
                return False
        return True

    def unpack_payload(self, flatten=False):
        self.create_unpacking_dir()
        self.unpack_files(self.payload, flatten)

    def pickle_dump(self) -> bytes:
        return pickle.dumps(self)
    
    @staticmethod
    def pickle_load(data : bytes): # returns Payload type
        return pickle.loads(data)



if __name__ == "__main__":
    f=Payload()
    f.get_files()
    print(f.payload)
    # f=paths.remove_dot_slash("./fff/tt.txt")
    # print(f)