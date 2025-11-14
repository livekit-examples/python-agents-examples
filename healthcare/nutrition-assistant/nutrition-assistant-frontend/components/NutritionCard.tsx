"use client";

import { useEffect, useState } from "react";
import { useMaybeRoomContext } from "@livekit/components-react";
import { RpcInvocationData } from "livekit-client";

interface Food {
  food_name: string;
  consumed_at: string;
  calories: number | null;
  protein: number | null;
  carbs: number | null;
  fats: number | null;
}

interface NutritionData {
  foods: Food[];
  totals: {
    calories: number;
    protein: number;
    carbs: number;
    fats: number;
  };
  date: string;
}

export default function NutritionCard() {
  const [nutritionData, setNutritionData] = useState<NutritionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const room = useMaybeRoomContext();

  useEffect(() => {
    if (!room || !room.localParticipant) return;

    const handleNutritionUpdate = async (rpcInvocation: RpcInvocationData): Promise<string> => {
      try {
        // Parse the payload (it comes as a JSON string from Python)
        const payload = JSON.parse(rpcInvocation.payload);
        
        if (payload) {
          setNutritionData(payload);
          setError(null);
          setIsLoading(false);
          return "Success: Nutrition data updated";
        } else {
          return "Error: Invalid nutrition data format";
        }
      } catch (error) {
        setError("Failed to parse nutrition data");
        return "Error: " + (error instanceof Error ? error.message : String(error));
      }
    };

    // Register RPC method
    room.localParticipant.registerRpcMethod("nutrition.update", handleNutritionUpdate);

    // Set loading to false after a short timeout if no data received
    const timeout = setTimeout(() => {
      if (isLoading) {
        setIsLoading(false);
      }
    }, 2000);

    return () => {
      if (room && room.localParticipant) {
        room.localParticipant.unregisterRpcMethod("nutrition.update");
      }
      clearTimeout(timeout);
    };
  }, [room, isLoading]);

  if (isLoading) {
    return (
      <div className="w-[512px] max-w-[90vw] mx-auto bg-gray-800/50 rounded-lg p-6 backdrop-blur-sm">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-3/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-[512px] max-w-[90vw] mx-auto bg-red-900/20 rounded-lg p-6 backdrop-blur-sm">
        <p className="text-red-400">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="w-[512px] max-w-[90vw] mx-auto bg-gray-800/50 rounded-lg p-6 backdrop-blur-sm">
      <h2 className="text-xl font-semibold mb-4">Today's Nutrition</h2>
      
      {/* Daily Totals */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-700/50 rounded-lg p-4">
          <p className="text-sm text-gray-400">Calories</p>
          <p className="text-2xl font-bold text-green-400">
            {nutritionData?.totals.calories.toFixed(0) || 0}
          </p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-4">
          <p className="text-sm text-gray-400">Protein</p>
          <p className="text-2xl font-bold text-blue-400">
            {nutritionData?.totals.protein.toFixed(1) || 0}g
          </p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-4">
          <p className="text-sm text-gray-400">Carbs</p>
          <p className="text-2xl font-bold text-yellow-400">
            {nutritionData?.totals.carbs.toFixed(1) || 0}g
          </p>
        </div>
        <div className="bg-gray-700/50 rounded-lg p-4">
          <p className="text-sm text-gray-400">Fats</p>
          <p className="text-2xl font-bold text-purple-400">
            {nutritionData?.totals.fats.toFixed(1) || 0}g
          </p>
        </div>
      </div>

      {/* Food List */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-400 mb-2">Foods Consumed</h3>
        <div className="max-h-[200px] overflow-y-auto space-y-2">
          {nutritionData?.foods.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No foods logged today</p>
          ) : (
            nutritionData?.foods.map((food, index) => (
              <div
                key={index}
                className="bg-gray-700/30 rounded-md p-3 flex justify-between items-center"
              >
                <div>
                  <p className="font-medium">{food.food_name}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(food.consumed_at).toLocaleTimeString()}
                  </p>
                </div>
                <div className="text-right text-sm">
                  {food.calories && (
                    <p className="text-green-400">{food.calories.toFixed(0)} cal</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}