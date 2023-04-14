Note:Due to constraints on my office machine creating an executable had some problem while include pytube.
So, you can try running the exe in dist folder but if has some problem try to run main.py seprately and then testing files can be run to test.


File & Folder Details:

1) main.py file has the flask service overlay_stitching which takes the youtube url and overlay png image path
2) Test_Concurrent_Requests.py: Concurrently raises multiple requests to the services which are handled parallely by the service with max_worker thread number 4.
3) Test_Sequential_Requests.py: By this file you can test any number of url request which will be proccessed 1 by 1.
4) requirements.txt: This file is exported from pycharm with all dependency packages used to run this main.py
5) output: It is folder where all the files get downloaded and processed.
6) Inside output folder ::: chunk_* folder will have normal video chunks.
7) Inside output folder ::: Input_*_Overlay_chunks_* folder will have video chunks with overlayed image.
8) Inside output folder ::: Input_*_Overlayed_output_ts_files folder will have ts segments of overlayed video.
9) Inside output folder ::: Input_*_Overlayed_output.mp4 will be whole video with overlay as final output.	



How to run:

1) Try to run main.py as it will start the service.
   You can use pycharm or python prompt or try to run exe in dist folder.
2) For any package issues refer to requirements.txt file or you can do pip install -r requirements.txt to add all dependencies.
3) After the main.py starts the service will start at localhost port:8888, 
4) Now you can test the service via Test files shared.
   Before running them check the url list and overlay.png image path in the scripts and set them.
   Then go ahead and run Test_Concurrent_Requests.py or Test_Sequential_Requests.py
   You will see files creation in outpput folder.

Note:All functions inside main.py have comments about their functionality please read through it.