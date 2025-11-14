import { useEffect, useState } from "react";
import { useMediaDeviceSelect } from "@livekit/components-react";
import { ChevronDown } from "lucide-react";

type DeviceSelectorProps = {
  kind: MediaDeviceKind;
};

export const DeviceSelector = ({ kind }: DeviceSelectorProps) => {
  const [showMenu, setShowMenu] = useState(false);
  const deviceSelect = useMediaDeviceSelect({ kind: kind });
  const [selectedDeviceName, setSelectedDeviceName] = useState("");

  useEffect(() => {
    deviceSelect.devices.forEach((device) => {
      if (device.deviceId === deviceSelect.activeDeviceId) {
        setSelectedDeviceName(device.label);
      }
    });
  }, [deviceSelect.activeDeviceId, deviceSelect.devices, selectedDeviceName]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      void event;
      if (showMenu) {
        setShowMenu(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, [showMenu]);

  const activeClassName = showMenu ? "rotate-180" : "rotate-0";

  return (
    <div className="relative">
      <button
        className={`flex hover:opacity-50 ${activeClassName} transition-all duration-100`}
        onClick={(e) => {
          setShowMenu(!showMenu);
          e.stopPropagation();
        }}
      >
        <ChevronDown className="w-4 h-4 text-accent-text" />
      </button>
      <div
        className="absolute bg-accent-bg left-0 bottom-8 text-[#424049] text-left border-white/20 border-[1px] box-border rounded-[5px] z-10 w-[280px]"
        style={{
          display: showMenu ? "block" : "none",
        }}
      >
        {deviceSelect.devices.map((device, index) => {
          const isFirst = index === 0;
          const isLast = index === deviceSelect.devices.length - 1;

          let roundedStyles = "";
          if (isFirst) {
            roundedStyles = " rounded-t-[5px]";
          } else if (isLast) {
            roundedStyles = " rounded-b-[5px]";
          }

          return (
            <div
              onClick={(e) => {
                e.stopPropagation();
                deviceSelect.setActiveMediaDevice(device.deviceId);
                setShowMenu(false);
              }}
              className={`${device.deviceId === deviceSelect.activeDeviceId
                ? "text-white"
                : "text-white"
                }  text-xs py-2 px-2 cursor-pointer hover:bg-white/10 ${roundedStyles}`}
              key={index}
            >
              {device.label}
            </div>
          );
        })}
      </div>
    </div>
  );
};
