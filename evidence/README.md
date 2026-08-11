# Runtime Evidence Checklist


1. `docker compose ps` output showing:
   - `namenode`
   - `datanode1` through `datanode10`


   ![alt text](image.png)



2. HDFS health report:

   ```powershell
   docker exec namenode hdfs dfsadmin -report > evidence\hdfs-report.txt
   ```
   ![alt text](image-1.png)
   ![alt text](image-2.png)
   ![alt text](image-3.png)
   ![alt text](image-4.png)
   ![alt text](image-5.png)
   ![alt text](image-6.png)
   ![alt text](image-7.png)
   ![alt text](image-8.png)



3. HDFS file listing after upload:

   ```powershell
   docker exec namenode hdfs dfs -ls /data > evidence\hdfs-data-listing.txt
   ```
   ![alt text](image-9.png)
   ![alt text](image-10.png)



4. Upload script output:

   ```powershell
   python upload_to_hdfs.py --namenode http://localhost:9870 --local-dir ./data > evidence\upload-output.txt
   ```
   ![alt text](image-11.png)


5. Verification script output:

   ```powershell
   python verify_hdfs.py --namenode http://localhost:9870 --local-dir ./data > evidence\verify-output.txt
   ```
   ![alt text](image-12.png)



6. screenshot of `http://localhost:9870` :
   - Namenode web UI showing the live datanodes.
   ![alt text](image-13.png)


7. setup hdfs structure

![alt text](image-14.png)


8.to run jobs

![alt text](image-16.png)
![alt text](image-17.png)
![alt text](image-18.png)
![alt text](image-19.png)
job1 
![alt text](image-20.png)
job2 
![alt text](image-21.png)
