import React, { useState, useEffect, useRef } from 'react';

const ParticipantList = ({ participants }) => {
  const [imageLoadingStates, setImageLoadingStates] = useState([]);
  const imgRefs = useRef([]);

  useEffect(() => {
    setImageLoadingStates(participants.map(() => true));
    imgRefs.current = participants.map(() => React.createRef());
  }, [participants]);

  useEffect(() => {
    // Check for already loaded images (cached images)
    const timer = setTimeout(() => {
      imgRefs.current.forEach((ref, index) => {
        if (ref.current && ref.current.complete && ref.current.naturalHeight !== 0) {
          handleImageLoad(index);
        }
      });
    }, 100); // Small delay to ensure refs are set

    return () => clearTimeout(timer);
  }, [participants]);

  const handleImageLoad = (index) => {
    setImageLoadingStates(prev => {
      const newStates = [...prev];
      newStates[index] = false;
      return newStates;
    });
  };

  const handleImageError = (index) => {
    setImageLoadingStates(prev => {
      const newStates = [...prev];
      newStates[index] = false;
      return newStates;
    });
  };

  return (
    <div className="participant-list">
      {participants.map((participant, index) => (
        <div key={index} className="participant">
          {imageLoadingStates[index] && (
            <div className="shimmer"></div>
          )}
          <img
            ref={imgRefs.current[index]}
            src={participant.image}
            alt={participant.name}
            onLoad={() => handleImageLoad(index)}
            onError={() => handleImageError(index)}
            style={{ display: imageLoadingStates[index] ? 'none' : 'block' }}
          />
          <p>{participant.name}</p>
        </div>
      ))}
    </div>
  );
};

export default ParticipantList;
