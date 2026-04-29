1. Train Serve Skew
*Challenges Faced:*
After running Training Pipeline on CIC-IDS2017 dataset(which is consisdered one of the most famous NIDS Dataset in the World), LightGBM model scored had amazing metrics in evaluation, but when the system was tested at inference the model completely failed.
*Solution:*
After a through research, it was found that there were huge flaws in CIC-IDS2017 Dataset and Tool CICFlowMeter. [A detailed Research and Outcomes report that contains why I faced Train Serve Skew and what solution is founded, Please read here](./Research%20and%20Outcomes/Readme.md)

2. Working with LycosStand