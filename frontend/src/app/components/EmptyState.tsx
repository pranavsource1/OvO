"use client";

import { motion } from "framer-motion";
import { Music, Waves, Upload } from "lucide-react";

interface EmptyStateProps {
  onUploadClick?: () => void;
}

export default function EmptyState({ onUploadClick }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 300 }}
      className="flex flex-col items-center justify-center py-24 text-center"
    >
      {/* Animated floating music icon */}
      <motion.div
        className="relative mb-8"
        animate={{
          y: [0, -8, 0],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {/* Outer glow ring */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(34,211,238,0.15) 0%, transparent 70%)",
            transform: "scale(2.5)",
          }}
          animate={{
            scale: [2.5, 3, 2.5],
            opacity: [0.5, 0.8, 0.5],
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Icon container */}
        <div
          className="relative w-20 h-20 rounded-2xl flex items-center justify-center"
          style={{
            background:
              "linear-gradient(135deg, rgba(34,211,238,0.1), rgba(139,92,246,0.1))",
            border: "1px solid rgba(255,255,255,0.08)",
            boxShadow: "0 0 40px rgba(34,211,238,0.1)",
          }}
        >
          <Music size={32} style={{ color: "rgba(255,255,255,0.4)" }} />
        </div>

        {/* Floating wave particles */}
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute"
            style={{
              top: "50%",
              left: "50%",
            }}
            animate={{
              x: [0, Math.cos((i * 120 * Math.PI) / 180) * 40],
              y: [0, Math.sin((i * 120 * Math.PI) / 180) * 40],
              opacity: [0, 0.6, 0],
              scale: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              delay: i * 0.8,
              ease: "easeInOut",
            }}
          >
            <Waves size={14} style={{ color: "#22d3ee" }} />
          </motion.div>
        ))}
      </motion.div>

      {/* Text */}
      <h3
        className="text-lg font-semibold mb-2"
        style={{ color: "rgba(255,255,255,0.7)" }}
      >
        No ideas yet
      </h3>
      <p
        className="text-sm max-w-xs mx-auto mb-8"
        style={{ color: "rgba(255,255,255,0.3)" }}
      >
        Drop your first .wav file to start building your musical evolution tree.
      </p>

      {/* Upload CTA */}
      <motion.button
        onClick={onUploadClick}
        whileHover={{ scale: 1.04, y: -2 }}
        whileTap={{ scale: 0.97 }}
        className="flex items-center gap-2.5 px-6 py-3 rounded-xl text-sm font-semibold cursor-pointer"
        style={{
          background:
            "linear-gradient(135deg, rgba(34,211,238,0.15), rgba(139,92,246,0.15))",
          border: "1px solid rgba(34,211,238,0.25)",
          color: "#22d3ee",
          boxShadow: "0 0 30px rgba(34,211,238,0.1)",
        }}
      >
        <Upload size={16} />
        Upload your first idea
      </motion.button>
    </motion.div>
  );
}
