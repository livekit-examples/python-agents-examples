"use client";

import React, { createContext, useCallback, useState } from "react";

const TOKEN_ENDPOINT = "/api/token";

type TokenGeneratorData = {
  shouldConnect: boolean;
  wsUrl: string;
  token: string;
  disconnect: () => Promise<void>;
  connect: () => Promise<void>;
};

const ConnectionContext = createContext<TokenGeneratorData | undefined>(
  undefined,
);

export const ConnectionProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [connectionDetails, setConnectionDetails] = useState<{
    wsUrl: string;
    token: string;
    shouldConnect: boolean;
  }>({ wsUrl: "", token: "", shouldConnect: false });

  const connect = async () => {
    if (!process.env.NEXT_PUBLIC_LIVEKIT_URL) {
      throw new Error("NEXT_PUBLIC_LIVEKIT_URL is not set");
    }
    const { accessToken } = await fetch(TOKEN_ENDPOINT).then((res) =>
      res.json(),
    );
    setConnectionDetails({
      wsUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL,
      token: accessToken,
      shouldConnect: true,
    });
  };

  const disconnect = useCallback(async () => {
    setConnectionDetails((prev) => ({ ...prev, shouldConnect: false }));
  }, []);

  return (
    <ConnectionContext.Provider
      value={{
        wsUrl: connectionDetails.wsUrl,
        token: connectionDetails.token,
        shouldConnect: connectionDetails.shouldConnect,
        connect,
        disconnect,
      }}
    >
      {children}
    </ConnectionContext.Provider>
  );
};

export const useConnection = () => {
  const context = React.useContext(ConnectionContext);
  if (context === undefined) {
    throw new Error("useConnection must be used within a ConnectionProvider");
  }
  return context;
};
