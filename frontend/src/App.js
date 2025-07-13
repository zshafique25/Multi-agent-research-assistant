// frontend/src/App.js
import React, { useState } from 'react';
import {
  ChakraProvider,
  Container,
  Box,
  Heading,
  Text,
  VStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Divider,
} from '@chakra-ui/react';
import ResearchForm from './components/ResearchForm';
import ResearchStatus from './components/ResearchStatus';
import ResearchResults from './components/ResearchResults';

function App() {
  const [activeResearchId, setActiveResearchId] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState(0);

  const handleResearchStarted = (researchId) => {
    setActiveResearchId(researchId);
    setResult(null);
    setActiveTab(1); // Switch to status tab
  };

  const handleStatusUpdate = (status) => {
    if (status.status === 'complete' && status.result) {
      setResult(status.result);
      setActiveTab(2); // Switch to results tab
    }
  };

  return (
    <ChakraProvider>
      <Container maxW="container.lg" py={8}>
        <VStack spacing={8} align="stretch">
          <Box textAlign="center">
            <Heading as="h1" size="xl">Cerebral Collective</Heading>
            <Text mt={2} color="gray.600">
              A multi-agent AI system for comprehensive research
            </Text>
          </Box>

          <Divider />

          <Tabs index={activeTab} onChange={setActiveTab} variant="enclosed" colorScheme="blue">
            <TabList>
              <Tab>Start Research</Tab>
              <Tab isDisabled={!activeResearchId}>Progress</Tab>
              <Tab isDisabled={!result}>Results</Tab>
            </TabList>

            <TabPanels>
              <TabPanel>
                <ResearchForm onResearchStarted={handleResearchStarted} />
              </TabPanel>
              <TabPanel>
                {activeResearchId && (
                  <ResearchStatus 
                    researchId={activeResearchId} 
                    onStatusUpdate={handleStatusUpdate}
                  />
                )}
              </TabPanel>
              <TabPanel>
                {result && <ResearchResults result={result} />}
              </TabPanel>
            </TabPanels>
          </Tabs>
        </VStack>
      </Container>
    </ChakraProvider>
  );
}

export default App;