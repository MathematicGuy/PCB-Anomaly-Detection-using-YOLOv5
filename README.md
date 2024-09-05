### Common bugs

+ Convert Yolov5 Weight for Linux to Torch value Weight for Windows. which leading to NotImplementedError: cannot instantiate 'PosixPath' on your system" error
+ "/" is for Linux, "\\" is for Windows

### Run
Intall FastAPI Cli

cd backend
+ fastapi dev (for debugging)
+ fastapi run (for production)


### File
runs/detect/exp/
test1.txt
text2.txt

for "test1.txt" structure:
```html
<class> <confidence> <bounding box coordinates>
2       0.85         54 18 221 322
0       0.92         30 44 200 300
```
