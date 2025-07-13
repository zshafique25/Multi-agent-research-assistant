/ frontend/src/components/ResearchStatus.js
import React, { useEffect, useState } from 'react';
import {
  Box,
  Heading,
  Text,
  Progress,
  VStack,
  HStack,
  Badge,
  Spinner,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import { getResearchStatus, getResearchMessages } from '../services/api';

const ResearchStatus = ({ researchId }) => {
  const [status, setStatus] = useState({});
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!researchId) return;

    const fetchStatus = async () => {
      try {
        const statusData = await getResearchStatus(researchId);
        setStatus(statusData);
        
        const messagesData = await getResearchMessages(researchId);
        setMessages(messagesData.messages);
        
        setLoading(false);
        
        // Continue polling if not complete
        if (statusData.status !== 'complete') {
          setTimeout(fetchStatus, 5000);
        }
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchStatus();
  }, [researchId]);

  if (loading) {
    return (
      <Box p={6} borderWidth="1px" borderRadius="lg" bg="white" shadow="md" textAlign="center">
        <Spinner size="xl" />
        <Text mt={4}>Loading research status...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={6} borderWidth="1px" borderRadius="lg" bg="white" shadow="md">
        <Heading as="h3" size="md" color="red.500">
          Error
        </Heading>
        <Text mt={2}>{error}</Text>
      </Box>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'planning':
        return 'blue';
      case 'researching':
        return 'purple';
      case 'analyzing':
        return 'orange';
      case 'reporting':
        return 'teal';
      case 'complete':
        return 'green';
      default:
        return 'gray';
    }
  };

  const getAgentColor = (agent) => {
    switch (agent) {
      case 'manager':
        return 'blue';
      case 'retrieval':
        return 'purple';
      case 'analysis':
        return 'orange';
      case 'evaluation':
        return 'teal';
      case 'report':
        return 'green';
      default:
        return 'gray';
    }
  };

  return (
    <Box p={6} borderWidth="1px" borderRadius="lg" bg="white" shadow="md">
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Heading as="h3" size="md">
            Research Progress
          </Heading>
          <Badge colorScheme={getStatusColor(status.status)} fontSize="md" py={1} px={2} borderRadius="md">
            {status.status?.toUpperCase()}
          </Badge>
        </HStack>

        <Progress 
          value={status.progress * 100} 
          size="lg" 
          colorScheme={getStatusColor(status.status)}
          borderRadius="md"
          hasStripe={status.status !== 'complete'}
          isAnimated={status.status !== 'complete'}
        />

        <Text>
          {status.status === 'complete' 
            ? 'Research completed!' 
            : `Estimated completion: ${status.estimated_completion}`}
        </Text>

        <Accordion allowToggle defaultIndex={[0]}>
          <AccordionItem>
            <h2>
              <AccordionButton>
                <Box flex="1" textAlign="left" fontWeight="bold">
                  Agent Activity Log
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack spacing={2} align="stretch" maxH="300px" overflowY="auto">
                {messages.map((msg, index) => (
                  <HStack key={index} p={2} borderWidth="1px" borderRadius="md">
                    <Badge colorScheme={getAgentColor(msg.agent)}>
                      {msg.agent || 'system'}
                    </Badge>
                    <Text flex="1">{msg.content}</Text>
                  </HStack>
                ))}
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
      </VStack>
    </Box>
  );
};

export default ResearchStatus;