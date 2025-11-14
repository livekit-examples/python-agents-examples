import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';
import '@livekit/components-styles';
import { useVoiceAssistant, BarVisualizer, VoiceAssistantControlBar, useDataChannel } from "@livekit/components-react";
import { Room, RoomEvent, RemoteParticipant, DataPacket_Kind } from 'livekit-client';
import { useState, useEffect } from 'react';
import './App.css';

function CustomControlBar({ isConnected, onConnect, onDisconnect }: { 
  isConnected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}) {
  if (isConnected) {
    return <VoiceAssistantControlBar />;
  }
  
  return (
    <div className="lk-control-bar">
      <button 
        className="lk-button connect-button"
        onClick={onConnect}
      >
        Connect
      </button>
    </div>
  );
}

function SimpleVoiceAssistant({ 
  isConnected, 
  onConnect, 
  onDisconnect,
  currentRoomName
}: { 
  isConnected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
  onCallResponse: (roomInfo: { name: string; token: string }) => void;
  currentRoomName: string;
}) {
  const { state, audioTrack } = useVoiceAssistant();
  const [room, setRoom] = useState<Room | null>(null);
  const [phoneNumber, setPhoneNumber] = useState('+16136136136');
  const [task, setTask] = useState('');
  const [taskSubmitted, setTaskSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [callStatus, setCallStatus] = useState<'idle' | 'calling' | 'connecting'>('idle');
  const [dtmfCode, setDtmfCode] = useState<string | null>(null);

  // Use the data channel hook for DTMF updates
  useDataChannel('dtmf_code', (message) => {
    const code = new TextDecoder().decode(message.payload);
    setDtmfCode(code);
  });

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    if (dtmfCode !== null) {
      // Clear the DTMF code after 3 seconds
      timeout = setTimeout(() => {
        setDtmfCode(null);
      }, 3000);
    }
    return () => {
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  }, [dtmfCode]);

  const handleTaskSubmit = () => {
    if (task.trim()) {
      setTaskSubmitted(true);
    }
  };

  const handleCall = async () => {
    if (!phoneNumber || !currentRoomName || !task) return;
    
    setIsLoading(true);
    setCallStatus('calling');
    try {
      const response = await fetch('http://localhost:5001/api/call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          room_name: currentRoomName,
          task: task,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to initiate call');
      }

      const data = await response.json();
      console.log('Call initiated:', data);
      
      if (data.status === 'success') {
        setCallStatus('connecting');
        // Clear the phone number after successful call, but keep the task displayed
        setPhoneNumber('');
      }
    } catch (error) {
      console.error('Error initiating call:', error);
      setCallStatus('idle');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="content-wrapper">
        <div className="visualizer-container">
          <BarVisualizer
            state={state}
            barCount={7}
            trackRef={audioTrack}
            style={{ width: '100%', height: '200px' }}
          />
          <div className="dtmf-display-container">
            {dtmfCode && (
              <div className={`dtmf-display ${dtmfCode ? 'visible' : ''}`}>
                DTMF Code pressed: {dtmfCode}
              </div>
            )}
          </div>
        </div>
        <div className="control-container">
          <div className="lk-agent-control-bar">
            <CustomControlBar 
              isConnected={isConnected}
              onConnect={onConnect}
              onDisconnect={onDisconnect}
            />
          </div>
          <div className="call-controls">
            {/* Always show the task display if taskSubmitted is true */}
            {taskSubmitted && (
              <div className="task-display">Task: {task}</div>
            )}

            {/* Show the connected status if callStatus is 'connecting' */}
            {callStatus === 'connecting' && (
              <div className="connected-status">Connected to IVR</div>
            )}

            {/* Show the task input and submit button if task is not submitted AND callStatus is idle */}
            {!taskSubmitted && callStatus === 'idle' && (
              <div className="task-input-container">
                <input
                  type="text"
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  placeholder="Enter task description"
                  className="lk-form-control"
                  disabled={callStatus !== 'idle'}
                />
                <button 
                  className="lk-button" 
                  onClick={handleTaskSubmit}
                  disabled={!task.trim() || callStatus !== 'idle'}
                >
                  Submit Task
                </button>
              </div>
            )}

            {/* Show the phone number input and call button if task is submitted AND callStatus is not 'connecting' */}
            {taskSubmitted && callStatus !== 'connecting' && (
              <>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="Enter phone number"
                  className="lk-form-control"
                  disabled={callStatus !== 'idle'}
                />
                <button 
                  className="lk-button" 
                  onClick={handleCall}
                  disabled={isLoading || !phoneNumber || callStatus !== 'idle'}
                >
                  {callStatus === 'calling' ? 'Calling...' : 'Call'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const serverUrl = import.meta.env.VITE_LIVEKIT_URL || '';
  const [token, setToken] = useState('');
  const [roomName, setRoomName] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  const handleDisconnect = () => {
    setToken('');
    setIsConnected(false);
  };

  const handleConnect = async () => {
    const newRoomName = `room-${Math.random().toString(36).substring(7)}`;
    const identity = `user-${Math.random().toString(36).substring(7)}`;
    setRoomName(newRoomName);
    
    try {
      const response = await fetch('http://localhost:5001/api/generate-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_name: newRoomName,
          identity: identity,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get token');
      }

      const data = await response.json();
      if (data.token) {
        setToken(data.token);
        setIsConnected(true);
      }
    } catch (error) {
      console.error('Error getting token:', error);
    }
  };

  const handleCallResponse = (roomInfo: { name: string; token: string }) => {
    setRoomName(roomInfo.name);
    setToken(roomInfo.token);
    setIsConnected(true);
  };

  return (
    <LiveKitRoom
      audio={true}
      token={token}
      serverUrl={serverUrl}
      data-lk-theme="default"
      style={{ height: '100vh' }}
      onDisconnected={handleDisconnect}
    >
      <SimpleVoiceAssistant 
        isConnected={isConnected}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
        onCallResponse={handleCallResponse}
        currentRoomName={roomName}
      />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}
