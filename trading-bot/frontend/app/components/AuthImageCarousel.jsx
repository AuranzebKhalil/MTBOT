"use client";
import React, { useState, useEffect } from "react";

const images = [
  "/authImage/img1.jpg",
  "/authImage/img2.jpg",
  "/authImage/img3.jpg"
];

export default function AuthImageCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % images.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      width: "100%",
      height: "100%",
      position: "relative",
      overflow: "hidden",
      background: "#000"
    }}>
      {images.map((img, index) => (
        <div
          key={img}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            opacity: index === currentIndex ? 1 : 0,
            transition: "opacity 1.5s ease-in-out",
            zIndex: index === currentIndex ? 1 : 0,
          }}
        >
          <img
            src={img}
            alt={`Auth slide ${index}`}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              filter: "brightness(0.7) contrast(1.1)"
            }}
          />
          <div style={{
            position: "absolute",
            bottom: "0",
            left: "0",
            width: "100%",
            height: "50%",
            background: "linear-gradient(to top, rgba(0,0,0,0.8), transparent)",
            zIndex: 2
          }} />
        </div>
      ))}

      {/* Overlay Content */}
      <div style={{
        position: "absolute",
        bottom: "80px",
        left: "60px",
        zIndex: 10,
        maxWidth: "500px"
      }}>
        <h2 style={{
          color: "white",
          fontSize: "3.5rem",
          fontWeight: "900",
          lineHeight: "1.1",
          marginBottom: "20px",
          letterSpacing: "-2px"
        }}>
          Master the <span style={{ color: "var(--primary)" }}>Markets</span> with AI
        </h2>
        <p style={{
          color: "rgba(255,255,255,0.7)",
          fontSize: "1.2rem",
          lineHeight: "1.6"
        }}>
          Join thousands of operators using Auralith to automate their institutional trading strategies with millisecond precision.
        </p>
        
        <div style={{ display: "flex", gap: "10px", marginTop: "30px" }}>
          {images.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === currentIndex ? "40px" : "8px",
                height: "8px",
                borderRadius: "4px",
                background: i === currentIndex ? "var(--primary)" : "rgba(255,255,255,0.3)",
                transition: "all 0.3s ease"
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
