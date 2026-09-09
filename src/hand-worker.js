import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';
import { toHands } from './gestures.js';
let detector;
self.onmessage=async({data})=>{
  try {
    if(data.type==='init') {
      const vision=await FilesetResolver.forVisionTasks(data.origin+'/vision',true);
      detector=await HandLandmarker.createFromOptions(vision,{
        baseOptions:{modelAssetPath:data.origin+'/models/hand_landmarker.task',delegate:'CPU'},
        runningMode:'VIDEO',numHands:2,minHandDetectionConfidence:.4,minHandPresenceConfidence:.4,minTrackingConfidence:.4,
      });
      self.postMessage({type:'ready'});
    }else if(data.type==='frame') {
      try {const result=detector.detectForVideo(data.frame,data.timestamp);self.postMessage({type:'hands',hands:toHands(result)});}
      finally{data.frame.close();}
    }
  } catch(error){self.postMessage({type:'error',message:error.message});}
};
