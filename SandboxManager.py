#!/usr/bin/python
#  coding=UTF-8

import string
import tempfile
import random
import os
import time
from zipfile import ZipFile

class SandboxManager():

    def __init__(self, config, connector):
        self.algorithm_root = config.get("sga", "algorithm_root")
        self.project_root = config.get("sga", "project_root")
        self.connector = connector
        return


    def get_algorithm(self, algorithm_prfx):

        res_dir = os.path.join(self.algorithm_root, algorithm_prfx)
        if not os.path.exists(res_dir):
            os.makedirs(res_dir)
        else:
            return res_dir

        for f in self.connector.list_algo_files(algorithm_prfx):

            f_path = os.path.dirname(os.path.join(self.algorithm_root,f))
            if not os.path.exists(f_path):
                os.makedirs(f_path)

            self.connector.download_file_to_algo(f, self.algorithm_root)

        # Dando permissões completas aos arquivos do algoritmo
        for dirpath, dirnames, filenames in os.walk(res_dir):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                os.chmod(path, 0o777)

        return res_dir


    def get_project(self, project_prfx, project_input_files):

        proj_sandbox = os.path.join(self.project_root, project_prfx)
        if not os.path.exists(proj_sandbox):
            os.makedirs(proj_sandbox)

        metadata_dir = os.path.join(proj_sandbox,".az_sga_proj_metadata")

        for f in project_input_files:

            f_path = os.path.dirname(os.path.join(proj_sandbox,f))
            if not os.path.exists(f_path):
                os.makedirs(f_path)

            self.connector.download_file_to_project(project_prfx, f, self.project_root)

            # Inclui o arquivo na pasta com os metadados básicos, para identificar arquivos a
            # a serem enviados de volta para o repositório
            if not os.path.exists(metadata_dir):
                os.makedirs(metadata_dir)

            # Arquivo de metadados:
            # Primeira linha: Timestamp da última modificação
            # Segunda linha: Tamanho do arquivo

            f_one = f.replace('/', '_').replace('\\', '_')

            metadata_file = os.path.join(metadata_dir, f_one)
            f_file = open(metadata_file, "w+")
            f_file.write(time.ctime(os.path.getmtime(os.path.join(proj_sandbox,f)))+"\n")
            f_file.write(str(os.path.getsize(os.path.join(proj_sandbox,f))))
            f_file.close()

        return proj_sandbox

    def upload_project_modified_files(self, project_prfx):

        proj_sandbox = os.path.join(self.project_root, project_prfx)

        metadata_dir = os.path.join(proj_sandbox, ".az_sga_proj_metadata")

        for dirpath, dirnames, filenames in os.walk(proj_sandbox):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if path.find(".az_sga_proj_metadata") >= 0:
                    continue
                rel_path = path.replace(proj_sandbox,'').lstrip('/').lstrip('\\')

                f_one = rel_path.replace('/', '_').replace('\\', '_')
                metadata_file = os.path.join(metadata_dir, f_one)
                need_upload = False
                if not os.path.exists(metadata_file):
                    need_upload = True
                else:
                    f_file = open(metadata_file, "r")
                    file_time = f_file.readline().replace('\n','').replace('\r','')
                    file_size = f_file.readline()
                    original_file_time = time.ctime(os.path.getmtime(os.path.join(proj_sandbox, path)))
                    if file_time != original_file_time:
                        need_upload = True

                    elif file_size != str(os.path.getsize(os.path.join(proj_sandbox,path))):
                        need_upload = True

                    f_file.close()

                if need_upload:
                    blob_name=os.path.join(project_prfx, (path.replace(proj_sandbox,'')))
                    self.connector.upload_proj_file(project_prfx, blob_name, self.project_root)

        return


    def __get_hash_of_dirs(directory, verbose=0):
      import hashlib, os
      sha_hash = hashlib.sha1()
      if not os.path.exists (directory):
        return -1

      try:
        for root, dirs, files in os.walk(directory):
          for names in files:
            if verbose == 1:
              print 'Hashing', names
            filepath = os.path.join(root,names)
            try:
              f1 = open(filepath, 'rb')
            except:
              # You can't open the file for some reason
              f1.close()
              continue

        while 1:
          # Read file in as little chunks
          buf = f1.read(4096)
          if not buf : break
          sha_hash.update(hashlib.sha1(buf).hexdigest())
        f1.close()

      except:
        import traceback
        # Print the stack traceback
        traceback.print_exc()
        return -2

      return sha_hash.hexdigest()
