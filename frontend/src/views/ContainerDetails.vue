<template>
  <div class="container-details">
    <top-bar title="Container Details">
    </top-bar>
    <v-container v-if="localState.container">
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-row>
            <v-col>
              <h1 class="justify-center d-flex">
                {{title}}
                <container-stars :container="localState.container"></container-stars>
                <v-badge :content="localState.container.downloadCount || '0'" inline color="blue-grey lighten-1" class="px-1">
                  <v-icon>mdi-download</v-icon>
                </v-badge>
                <a v-if="localState.container.vcsUrl" :href="localState.container.vcsUrl" class="text-decoration-none d-flex align-center">
                  <v-icon>mdi-source-repository</v-icon>
                </a>
              </h1>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input label="Name" :static-value="localState.container.name"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row dense>
            <v-col>
              <hsk-text-input label="Created" :static-value="localState.container.createdAt | moment('YYYY-MM-DD HH:mm:ss')"></hsk-text-input>
            </v-col>
            <v-col>
              <hsk-text-input label="Created By" :static-value="localState.container.createdBy"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input 
                label="Git/VCS URL" 
                field="vcsUrl" 
                :obj="localState.container" 
                action="containers/update"
                :readonly="!canEdit"
                @updated="localState.container=$event"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input 
                label="Description" 
                field="description" 
                :obj="localState.container" 
                action="containers/update"
                :readonly="!canEdit"
                @updated="localState.container=$event"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input 
                type="textarea"
                label="Full Description" 
                field="fullDescription" 
                :obj="localState.container" 
                action="containers/update"
                :readonly="!canEdit"
                @updated="localState.container=$event"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input
                type="yesno"
                label="Private"
                field="private"
                :obj="localState.container"
                action="containers/update"
                :readonly="!canEdit"
                @updated="localState.container=$event"></hsk-text-input>
            </v-col>
            <v-col>
              <hsk-text-input
                type="yesno"
                label="Readonly"
                field="readOnly"
                :obj="localState.container"
                action="containers/update"
                :readonly="!localState.container.canEdit(currentUser)"
                @updated="localState.container=$event"></hsk-text-input>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <h2 class="text-center mb-2">Images</h2>
          <v-expansion-panels inset>
            <image-details 
              v-for="image in images"
              :key="image.id"
              :readonly="localState.container.readOnly"
              :image="image"></image-details>
          </v-expansion-panels>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import ImageDetails from '@/components/ImageDetails.vue';
import Vue from 'vue';
import { Container, Image, User } from '../store/models';

interface State {
  container: Container | null;
}

export default Vue.extend({
  components: { ImageDetails, },
  name: 'ContainerDetails',
  mounted() {
    this.loadContainer();
  },
  data: (): { localState: State } => ({
    localState: {
      container: null,
    }
  }),
  watch: {
    $route() {
      this.loadContainer();
    }
  },
  computed: {
    title(): string {
      return `${this.localState.container ? this.localState.container.fullPath : '...'}`
    },
    loading(): boolean {
      return this.$store.getters['container/status']==='loading';
    },
    images(): Image[] {
      return this.$store.getters['images/list'];
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return !this.localState.container?.readOnly && this.localState.container!.canEdit(this.currentUser)
    }
  },
  methods: {
    loadContainer() {
      this.$store.dispatch('containers/get', { entityName: this.$route.params.entity, collectionName: this.$route.params.collection, containerName: this.$route.params.container })
        .then((container: Container) => {
          this.localState.container = container;
          return this.$store.dispatch('images/list', container);
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
  },
});
</script>